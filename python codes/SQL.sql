-- ------------------------------------------------
-- CREATE DATABASE
-- ------------------------------------------------
CREATE DATABASE IF NOT EXISTS AssetDB;
USE AssetDB;

-- ------------------------------------------------
-- USERS
-- ------------------------------------------------
CREATE TABLE IF NOT EXISTS Users (
    user_id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(100) NOT NULL,
    role ENUM('Admin','User') NOT NULL
);

INSERT IGNORE INTO Users (username, password, role) VALUES
('admin', 'admin123', 'Admin'),
('user1', 'user123', 'User');

-- ------------------------------------------------
-- DEPARTMENTS
-- ------------------------------------------------
CREATE TABLE IF NOT EXISTS Departments (
    dept_id INT PRIMARY KEY AUTO_INCREMENT,
    dept_name VARCHAR(100) NOT NULL
);

INSERT IGNORE INTO Departments (dept_name) VALUES 
('IT'), ('HR'), ('Finance');

-- ------------------------------------------------
-- EMPLOYEES (FINAL — NO empid ERROR)
-- ------------------------------------------------
CREATE TABLE IF NOT EXISTS Employees (
    employee_id INT PRIMARY KEY AUTO_INCREMENT,
    full_name VARCHAR(100) NOT NULL,
    department VARCHAR(100),
    job_title VARCHAR(100),
    email VARCHAR(100),
    phone VARCHAR(20),
    date_joined DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    
);

INSERT IGNORE INTO Employees (full_name, department, job_title, email, phone, date_joined) VALUES
('Ali Khan', 'IT', 'Developer', 'ali@example.com', '03001234567', '2024-05-11'),
('Sara Ahmed', 'HR', 'HR Manager', 'sara@example.com', '03007654321', '2024-01-02');

-- ------------------------------------------------
-- VENDORS
-- ------------------------------------------------
CREATE TABLE IF NOT EXISTS Vendors (
    vendor_id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    contact VARCHAR(100)
);

INSERT IGNORE INTO Vendors (name, contact) VALUES
('Tech Supplies Co.', 'tech@vendor.com'),
('Office Solutions', 'office@vendor.com');

-- ------------------------------------------------
-- ASSETS
-- ------------------------------------------------
CREATE TABLE IF NOT EXISTS Assets (
    asset_id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    category VARCHAR(50) NOT NULL,
    purchase_date DATE NOT NULL,
    cost DECIMAL(10,2) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'Available',
    location VARCHAR(100),
    description TEXT,
    warranty_end DATE,
    department_id INT NULL,
    FOREIGN KEY (department_id) REFERENCES Departments(dept_id)
        ON DELETE SET NULL
        ON UPDATE CASCADE
);

INSERT IGNORE INTO Assets (name, category, purchase_date, cost, location, description, warranty_end, department_id) VALUES
('Laptop Dell', 'Electronics', '2025-01-10', 1200.00, 'IT Office', 'Core development laptop', '2026-01-10', 1),
('Projector Epson', 'Electronics', '2024-12-05', 800.00, 'Conference Room', 'HD Projector', '2025-12-05', 2);

-- ------------------------------------------------
-- ASSET ASSIGNMENTS
-- ------------------------------------------------
CREATE TABLE IF NOT EXISTS AssetAssignments (
    assignment_id INT PRIMARY KEY AUTO_INCREMENT,
    asset_id INT,
    employee_id INT,
    assign_date DATE,
    return_date DATE,
    FOREIGN KEY (asset_id) REFERENCES Assets(asset_id),
    FOREIGN KEY (employee_id) REFERENCES Employees(employee_id)
);

-- ------------------------------------------------
-- MAINTENANCE
-- ------------------------------------------------
CREATE TABLE IF NOT EXISTS Maintenance (
    maintenance_id INT PRIMARY KEY AUTO_INCREMENT,
    asset_id INT,
    vendor_id INT,
    issue_desc TEXT,
    start_date DATE,
    end_date DATE,
    cost DECIMAL(10,2),
    FOREIGN KEY (asset_id) REFERENCES Assets(asset_id),
    FOREIGN KEY (vendor_id) REFERENCES Vendors(vendor_id)
);

-- ------------------------------------------------
-- AUDIT HISTORY 100% FIXED — NO WARNING EVER
-- ------------------------------------------------

-- Check existence safely
SET @tableExists = (
    SELECT COUNT(*) FROM information_schema.tables
    WHERE table_schema = 'AssetDB'
    AND table_name = 'AuditHistory'
);

-- Drop only if actually present
SET @sql = IF(@tableExists > 0, 
    'DROP TABLE AssetDB.AuditHistory', 
    'SELECT "AuditHistory does not exist"');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Create clean new table
CREATE TABLE AuditHistory (
    audit_id INT PRIMARY KEY AUTO_INCREMENT,
    asset_id INT NULL,
    action VARCHAR(100) NOT NULL,
    performed_by VARCHAR(50) NOT NULL,
    notes TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (asset_id) REFERENCES Assets(asset_id)
);

INSERT INTO AuditHistory (action, performed_by, notes)
VALUES ('System Start', 'admin', 'Audit initialized');