import sqlite3

DATABASE = 'crm.db'

def get_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS businesses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            type TEXT NOT NULL,
            city TEXT,
            website TEXT,
            instagram TEXT,
            status TEXT DEFAULT 'contacted',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS contacts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            business_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            phone TEXT,
            role TEXT,
            FOREIGN KEY (business_id) REFERENCES businesses(id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS interactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            business_id INTEGER NOT NULL,
            type TEXT NOT NULL,
            note TEXT,
            date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (business_id) REFERENCES businesses(id)
        )
    ''')

    conn.commit()
    conn.close()


# ===== BUSINESS FUNCTIONS =====


def add_business(name, type_, city, website, instagram):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO businesses (name, type, city, website, instagram)
        VALUES (?, ?, ?, ?, ?)
    ''', (name, type_, city, website, instagram))
    conn.commit()
    business_id = cursor.lastrowid
    conn.close()
    return business_id

def get_all_businesses():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM businesses
        ORDER BY created_at DESC
        ''')
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_businesses_by_status(status):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM businesses
        WHERE status = ?
        ORDER BY created_at DESC
    ''', (status,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def update_business_status(business_id, new_status):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE businesses
        SET status = ?
        WHERE id = ?
    ''', (new_status, business_id))
    conn.commit()
    conn.close()

def delete_business(business_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        DELETE FROM businesses
        WHERE id = ?
    ''', (business_id,))
    conn.commit()
    conn.close()


# ===== CONTACT FUNCTIONS =====

def add_contact(business_id, name, phone, role):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO contacts (business_id, name, phone, role)
        VALUES (?, ?, ?, ?)
    ''', (business_id, name, phone, role))
    conn.commit()
    contact_id = cursor.lastrowid
    conn.close()
    return contact_id

def get_contacts(business_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM contacts
        WHERE business_id = ?
    ''', (business_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]



# ===== INTERACTION FUNCTIONS =====

def add_interaction(business_id, type_, note):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO interactions (business_id, type, note)
        VALUES (?, ?, ?)
    ''', (business_id, type_, note))
    conn.commit()
    interaction_id = cursor.lastrowid
    conn.close()
    return interaction_id

def get_interactions(business_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM interactions 
        WHERE business_id = ?
        ORDER BY date DESC
    ''', (business_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


# ===== STATS =====

def get_stats():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM businesses")
    total = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM businesses WHERE status = 'interested'"
    )
    interested = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM businesses WHERE status = 'client'"
    )
    clients = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM businesses WHERE status = 'contacted'"
    )
    contacted = cursor.fetchone()[0]

    conn.close()
    return {
        "total": total,
        "contacted": contacted,
        "interested": interested,
        "clients": clients
    }
