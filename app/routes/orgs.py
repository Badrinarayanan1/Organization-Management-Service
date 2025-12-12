from fastapi import APIRouter, HTTPException, status, Depends
from app.models import OrgCreate, OrgOut, OrgUpdate
from app.db import get_db, create_org_collection, drop_org_collection
from app.utils import hash_password, verify_password
from app.auth import get_current_admin
from bson import ObjectId
from datetime import datetime


router = APIRouter(prefix="/org", tags=["org"])


@router.post("/create", response_model=OrgOut)
async def create_org(payload: OrgCreate):
    db = get_db()
    org_name = payload.organization_name.strip().lower()
    # ensure unique
    existing = await db.organizations.find_one({"organization_name": org_name})
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Organization already exists")

    collection_name = f"org_{org_name}"
    # create collection
    await create_org_collection(org_name)

    # create admin user
    admin_doc = {
        "email": payload.email,
        "password": hash_password(payload.password),
        "role": "admin",
        "organization": org_name,
    }
    res = await db.admins.insert_one(admin_doc)

    org_doc = {
        "organization_name": org_name,
        "collection_name": collection_name,
        "admin_id": str(res.inserted_id),
        "created_at": datetime.utcnow(),
    }
    await db.organizations.insert_one(org_doc)

    return {"organization_name": org_name, "collection_name": collection_name, "admin_id": str(res.inserted_id)}


@router.get("/get")
async def get_org(organization_name: str):
    db = get_db()
    org = await db.organizations.find_one({"organization_name": organization_name.strip().lower()})
    if not org:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")
    org["admin_id"] = str(org.get("admin_id"))
    if "_id" in org:
        org["_id"] = str(org["_id"])
    return org


@router.put("/update", response_model=OrgOut)
async def update_org(payload: OrgUpdate, current_admin: dict = Depends(get_current_admin)):
    db = get_db()
    
    # 1. Identify Target Org safely from Token
    target_org_name = current_admin["org_id"]
    
    # 2. Check if Org exists
    org = await db.organizations.find_one({"organization_name": target_org_name})
    if not org:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")

    new_org_name = payload.organization_name.strip().lower()
    
    # 3. Handle Rename
    if new_org_name != target_org_name:
        # Check uniqueness
        existing = await db.organizations.find_one({"organization_name": new_org_name})
        if existing:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="New organization name already exists")
        
        # Perform Metadata Updates
        # Update Org Record
        new_collection_name = f"org_{new_org_name}"
        await db.organizations.update_one(
            {"_id": org["_id"]}, 
            {"$set": {"organization_name": new_org_name, "collection_name": new_collection_name}}
        )
        # Update Admin Record (to point to new org)
        await db.admins.update_one(
            {"_id": ObjectId(current_admin["admin_id"])},
            {"$set": {"organization": new_org_name}}
        )
        
        # Perform Data Migration
        from app.db import rename_and_sync_collection
        await rename_and_sync_collection(target_org_name, new_org_name)
        
        # Update local variable for response
        target_org_name = new_org_name
        org["organization_name"] = new_org_name
        org["collection_name"] = new_collection_name

    # 4. Handle other updates (email/password)
    # Note: If email changes, the admin login ID changes.
    if payload.email or payload.password:
        update_fields = {}
        if payload.email:
            update_fields["email"] = payload.email
            await db.admins.update_one({"_id": ObjectId(current_admin["admin_id"])}, {"$set": {"email": payload.email}})
        if payload.password:
            await db.admins.update_one({"_id": ObjectId(current_admin["admin_id"])}, {"$set": {"password": hash_password(payload.password)}})

    # Return updated org
    updated_org = await db.organizations.find_one({"organization_name": target_org_name})
    updated_org["admin_id"] = str(updated_org["admin_id"])
    updated_org["_id"] = str(updated_org["_id"])
    return updated_org


@router.delete("/delete")
async def delete_org(organization_name: str, current_admin: dict = Depends(get_current_admin)):
    # 1. Strict Authorization
    # Ensure the admin is deleting THEIR OWN organization
    if current_admin["org_id"] != organization_name.strip().lower():
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not authorized to delete this organization")

    db = get_db()
    org_name = organization_name.strip().lower()
    org = await db.organizations.find_one({"organization_name": org_name})
    if not org:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")

    # delete collection
    await drop_org_collection(org_name)
    # delete admin
    await db.admins.delete_one({"_id": ObjectId(org["admin_id"])})
    # delete org metadata
    await db.organizations.delete_one({"organization_name": org_name})

    return {"status": "deleted"}
