# Organization Management Service

A backend system built using FastAPI and MongoDB to manage organizations in a multi-tenant architecture.
Each organization receives its own dynamically created MongoDB collection, while a Master Database stores global metadata and admin credentials.

This project is built as part of the Backend Intern Assignment.

## 📌 Features

- **Create organizations** with isolated collections (`org_<organization_name>`)
- **Store admin user info securely** (bcrypt hashing)
- **JWT authentication** for admin access
- **Update organization metadata** + rename/sync collections
- **Delete organizations and their collections** (admin-protected)
- **Modular, clean FastAPI code structure**

## 📁 Project Structure

```
Organization-Management-Service/
├── app/
│   ├── main.py
│   ├── db.py
│   ├── auth.py
│   ├── utils.py
│   ├── models.py
│   └── routes/
│        ├── orgs.py
│        └── admin.py
├── .env
├── requirements.txt
└── README.md
```

## 🚀 How the Multi-Tenant Architecture Works

When a new organization is created:

1.  **System validates org name**
2.  **System generates a sanitized collection name:** `org_<organization_name_in_lowercase>`
3.  **A new MongoDB collection is programmatically created**
4.  **Admin is created and stored in master DB with hashed password**
5.  **Master database stores:**
    -   org name
    -   collection name
    -   admin reference
6.  **API returns metadata for the new organization**

Every organization has isolated data, while core metadata is shared in a single master DB.

## 🔧 Tech Stack

-   **FastAPI** — Web framework
-   **Motor (Async MongoDB client)** — Database
-   **Passlib/Bcrypt** — Password hashing
-   **Python-Jose** — JWT authentication
-   **Uvicorn** — ASGI server

## 📄 Environment Variables (.env)

```env
MONGO_URI="YOUR_MONGO_URI"
MASTER_DB="master_org_db"
JWT_SECRET="YOUR_SECRET_KEY"
```

## ▶️ Running the Application

1.  **Install dependencies**
    ```bash
    pip install -r requirements.txt
    ```

2.  **Start FastAPI server**
    ```bash
    uvicorn app.main:app --reload
    ```

3.  **Open API Docs**
    [http://localhost:8000/docs](http://localhost:8000/docs)

## 🔌 API Reference

### 1. Create Organization
`POST /org/create`

**Request Body**
```json
{
  "organization_name": "AcmeCorp",
  "email": "admin@acme.com",
  "password": "admin123"
}
```

**What happens internally:**
- Validates uniqueness
- Creates collection: `org_acmecorp`
- Hashes password
- Creates admin user
- Saves metadata in organizations collection

**Response**
```json
{
  "organization_name": "acmecorp",
  "collection_name": "org_acmecorp",
  "admin_id": "67acbd..."
}
```

### 2. Get Organization
`GET /org/get?organization_name=AcmeCorp`

**Response**
```json
{
  "organization_name": "acmecorp",
  "collection_name": "org_acmecorp",
  "admin_id": "67acbd..."
}
```

### 3. Update Organization
`PUT /org/update`

**Request:**
```json
{
  "organization_name": "acmecorp",
  "email": "newadmin@acme.com",
  "password": "newpass123"
}
```

**Behavior:**
- Allows updating email/password
- Supports renaming org → triggers collection rename & sync

### 4. Delete Organization
`DELETE /org/delete?organization_name=acmecorp`

**Requires authentication:**
`Authorization: Bearer <jwt>`

**Behavior:**
- Validates admin token & organization
- Deletes:
    - dynamic org collection
    - admin user
    - organization metadata

**Response:**
```json
{ "status": "deleted" }
```

### 5. Admin Login
`POST /admin/login`

**Request:**
```json
{
  "email": "admin@acme.com",
  "password": "admin123"
}
```

**Response:**
```json
{
  "access_token": "<jwt-token>",
  "token_type": "bearer"
}
```

**Token contains:**
```json
{
  "admin_id": "id...",
  "org_id": "acmecorp"
}
```

## 🔐 Authentication Flow

1. Admin sends email + password
2. Password is verified using bcrypt
3. System retrieves linked organization
4. JWT token is generated containing:
    - `admin_id`
    - `org_id`
    - `expiration timestamp`
5. Token is required for protected endpoints
6. Token is validated via `HTTPBearer` in `get_current_admin`

## 🧠 High-Level Architecture Diagram

```
              ┌──────────────────────────────┐
              │          Client App           │
              └───────────────┬──────────────┘
                              │ HTTP
                              ▼
                    ┌───────────────────┐
                    │    FastAPI API    │
                    ├───────────────────┤
                    │ Routers:          │
                    │  - orgs.py        │
                    │  - admin.py       │
                    └───────┬───────────┘
                            │
                ┌───────────┴──────────────┐
                │        Master DB          │
                │ collections:              │
                │   - organizations         │
                │   - admins                │
                └───────────┬──────────────┘
                            │
     ┌──────────────────────────────────────────────────────┐
     │     Dynamic Collections (one per organization)       │
     │ ┌──────────────────────────────────────────────────┐ │
     │ │   org_acmecorp                                   │ │
     │ ├──────────────────────────────────────────────────┤ │
     │ │   org_foobar                                     │ │
     │ └──────────────────────────────────────────────────┘ │
     └──────────────────────────────────────────────────────┘
```

## 🏗️ Design Choices & Trade-offs

### ✔ Using a Single Mongo Database with Dynamic Collections

**Pros:**
- Simple to manage
- Easy to create/rename/delete per-org collections
- Fast for small to medium systems

**Cons:**
- No strong tenant isolation
- Large numbers of collections could affect performance

### ✔ Using JWT for Authentication
- Stateless
- Works well for microservice scaling
- Easy expiration and payload control

### ✔ Using Motor (async MongoDB driver)
- High throughput
- Plays perfectly with FastAPI async routes

## 💡 Potential Improvements
These are optional but show understanding of scalable design:

- Switch to "one database per tenant" for strong isolation
- Introduce role-based access control (RBAC)
- Add audit logs for organization lifecycle events
- Use background tasks for large collection renames
- Add caching layer (Redis) for faster org metadata lookups
- Add tests using pytest + mongomock

# Organization Management Service

A backend system built using FastAPI and MongoDB to manage organizations in a multi-tenant architecture.
Each organization receives its own dynamically created MongoDB collection, while a Master Database stores global metadata and admin credentials.

This project is built as part of the Backend Intern Assignment.

## 📌 Features

- **Create organizations** with isolated collections (`org_<organization_name>`)
- **Store admin user info securely** (bcrypt hashing)
- **JWT authentication** for admin access
- **Update organization metadata** + rename/sync collections
- **Delete organizations and their collections** (admin-protected)
- **Modular, clean FastAPI code structure**

## 📁 Project Structure

```
Organization-Management-Service/
├── app/
│   ├── main.py
│   ├── db.py
│   ├── auth.py
│   ├── utils.py
│   ├── models.py
│   └── routes/
│        ├── orgs.py
│        └── admin.py
├── .env
├── requirements.txt
└── README.md
```

## 🚀 How the Multi-Tenant Architecture Works

When a new organization is created:

1.  **System validates org name**
2.  **System generates a sanitized collection name:** `org_<organization_name_in_lowercase>`
3.  **A new MongoDB collection is programmatically created**
4.  **Admin is created and stored in master DB with hashed password**
5.  **Master database stores:**
    -   org name
    -   collection name
    -   admin reference
6.  **API returns metadata for the new organization**

Every organization has isolated data, while core metadata is shared in a single master DB.

## 🔧 Tech Stack

-   **FastAPI** — Web framework
-   **Motor (Async MongoDB client)** — Database
-   **Passlib/Bcrypt** — Password hashing
-   **Python-Jose** — JWT authentication
-   **Uvicorn** — ASGI server

## 📄 Environment Variables (.env)

```env
MONGO_URI="YOUR_MONGO_URI"
MASTER_DB="master_org_db"
JWT_SECRET="YOUR_SECRET_KEY"
```

## ▶️ Running the Application

1.  **Install dependencies**
    ```bash
    pip install -r requirements.txt
    ```

2.  **Start FastAPI server**
    ```bash
    uvicorn app.main:app --reload
    ```

3.  **Open API Docs**
    [http://localhost:8000/docs](http://localhost:8000/docs)

## 🔌 API Reference

### 1. Create Organization
`POST /org/create`

**Request Body**
```json
{
  "organization_name": "AcmeCorp",
  "email": "admin@acme.com",
  "password": "admin123"
}
```

**What happens internally:**
- Validates uniqueness
- Creates collection: `org_acmecorp`
- Hashes password
- Creates admin user
- Saves metadata in organizations collection

**Response**
```json
{
  "organization_name": "acmecorp",
  "collection_name": "org_acmecorp",
  "admin_id": "67acbd..."
}
```

### 2. Get Organization
`GET /org/get?organization_name=AcmeCorp`

**Response**
```json
{
  "organization_name": "acmecorp",
  "collection_name": "org_acmecorp",
  "admin_id": "67acbd..."
}
```

### 3. Update Organization
`PUT /org/update`

**Request:**
```json
{
  "organization_name": "acmecorp",
  "email": "newadmin@acme.com",
  "password": "newpass123"
}
```

**Behavior:**
- Allows updating email/password
- Supports renaming org → triggers collection rename & sync

### 4. Delete Organization
`DELETE /org/delete?organization_name=acmecorp`

**Requires authentication:**
`Authorization: Bearer <jwt>`

**Behavior:**
- Validates admin token & organization
- Deletes:
    - dynamic org collection
    - admin user
    - organization metadata

**Response:**
```json
{ "status": "deleted" }
```

### 5. Admin Login
`POST /admin/login`

**Request:**
```json
{
  "email": "admin@acme.com",
  "password": "admin123"
}
```

**Response:**
```json
{
  "access_token": "<jwt-token>",
  "token_type": "bearer"
}
```

**Token contains:**
```json
{
  "admin_id": "id...",
  "org_id": "acmecorp"
}
```

## 🔐 Authentication Flow

1. Admin sends email + password
2. Password is verified using bcrypt
3. System retrieves linked organization
4. JWT token is generated containing:
    - `admin_id`
    - `org_id`
    - `expiration timestamp`
5. Token is required for protected endpoints
6. Token is validated via `HTTPBearer` in `get_current_admin`

## 🧠 High-Level Architecture Diagram
![alt text](image-5.png)

## Working
![Create Organization API](image.png)
*Figure 1: Creating a new organization via the API.*

![Get Organization API](image-1.png)
*Figure 2: Retrieving details of an existing organization.*

![Update Organization API](image-2.png)
*Figure 3: Updating organization information and credentials.*

![Delete Organization API](image-3.png)
*Figure 4: Deleting an organization and its associated data.*

![Admin Login API](image-4.png)
*Figure 5: Admin authentication and JWT token generation.*


## 🏗️ Design Choices & Trade-offs

### ✔ Using a Single Mongo Database with Dynamic Collections

**Pros:**
- Simple to manage
- Easy to create/rename/delete per-org collections
- Fast for small to medium systems

**Cons:**
- No strong tenant isolation
- Large numbers of collections could affect performance

### ✔ Using JWT for Authentication
- Stateless
- Works well for microservice scaling
- Easy expiration and payload control

### ✔ Using Motor (async MongoDB driver)
- High throughput
- Plays perfectly with FastAPI async routes

## 💡 Potential Improvements
These are optional but show understanding of scalable design:

- Switch to "one database per tenant" for strong isolation
- Introduce role-based access control (RBAC)
- Add audit logs for organization lifecycle events
- Use background tasks for large collection renames
- Add caching layer (Redis) for faster org metadata lookups
- Add tests using pytest + mongomock
