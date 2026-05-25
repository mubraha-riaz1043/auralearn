-- ═══════════════════════════════════════
-- AuraLearn – MySQL Database Schema
-- All 14 Entities with FK Constraints
-- ═══════════════════════════════════════

CREATE DATABASE IF NOT EXISTS auralearn CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE auralearn;

-- 1. Category
CREATE TABLE Category (
    category_id INT AUTO_INCREMENT PRIMARY KEY,
    category_name VARCHAR(100) NOT NULL UNIQUE
);

-- 2. User Roles (helper table)
CREATE TABLE Role (
    role_id INT AUTO_INCREMENT PRIMARY KEY,
    role_name ENUM('admin','student','instructor') NOT NULL
);

-- 3. User
CREATE TABLE User (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    full_name VARCHAR(150) NOT NULL,
    email VARCHAR(200) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,         -- bcrypt hash
    role_id INT NOT NULL DEFAULT 2,          -- 2 = student
    profile_image VARCHAR(255) DEFAULT 'default.png',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (role_id) REFERENCES Role(role_id)
);

-- 4. Course
CREATE TABLE Course (
    course_id INT AUTO_INCREMENT PRIMARY KEY,
    course_name VARCHAR(200) NOT NULL,
    description TEXT,
    thumbnail VARCHAR(255),
    instructor_name VARCHAR(150),
    duration VARCHAR(50),
    price DECIMAL(8,2) DEFAULT 0.00,
    category_id INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (category_id) REFERENCES Category(category_id) ON DELETE SET NULL
);

-- 5. Enrollment
CREATE TABLE Enrollment (
    enroll_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    course_id INT NOT NULL,
    status ENUM('active','completed','suspended') DEFAULT 'active',
    progress_percentage DECIMAL(5,2) DEFAULT 0.00,
    enrolled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES User(user_id) ON DELETE CASCADE,
    FOREIGN KEY (course_id) REFERENCES Course(course_id) ON DELETE CASCADE,
    UNIQUE KEY unique_enrollment (user_id, course_id)
);

-- 6. Module
CREATE TABLE Module (
    module_id INT AUTO_INCREMENT PRIMARY KEY,
    course_id INT NOT NULL,
    module_title VARCHAR(200) NOT NULL,
    content TEXT,
    order_no INT DEFAULT 1,
    video_url VARCHAR(500),
    document_file VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (course_id) REFERENCES Course(course_id) ON DELETE CASCADE
);

-- 7. Zoom Classes
CREATE TABLE Zoom_Classes (
    class_id INT AUTO_INCREMENT PRIMARY KEY,
    course_id INT NOT NULL,
    class_title VARCHAR(200) NOT NULL,
    zoom_link VARCHAR(500),
    class_date DATETIME,
    instructor VARCHAR(150),
    FOREIGN KEY (course_id) REFERENCES Course(course_id) ON DELETE CASCADE
);

-- 8. Orders
CREATE TABLE Orders (
    order_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    module_id INT NOT NULL,
    price DECIMAL(8,2) NOT NULL,
    payment_status ENUM('pending','paid','failed','refunded') DEFAULT 'pending',
    from_date DATE,
    to_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES User(user_id) ON DELETE CASCADE,
    FOREIGN KEY (module_id) REFERENCES Module(module_id) ON DELETE CASCADE
);

-- 9. Questions
CREATE TABLE Questions (
    question_id INT AUTO_INCREMENT PRIMARY KEY,
    module_id INT NOT NULL,
    question_text TEXT NOT NULL,
    option_a VARCHAR(300),
    option_b VARCHAR(300),
    option_c VARCHAR(300),
    option_d VARCHAR(300),
    FOREIGN KEY (module_id) REFERENCES Module(module_id) ON DELETE CASCADE
);

-- 10. Solution
CREATE TABLE Solution (
    solution_id INT AUTO_INCREMENT PRIMARY KEY,
    question_id INT NOT NULL UNIQUE,
    correct_option ENUM('A','B','C','D') NOT NULL,
    solution_text TEXT,
    explanation TEXT,
    FOREIGN KEY (question_id) REFERENCES Questions(question_id) ON DELETE CASCADE
);

-- 11. Test
CREATE TABLE Test (
    test_id INT AUTO_INCREMENT PRIMARY KEY,
    module_id INT NOT NULL,
    total_marks INT DEFAULT 100,
    passing_marks INT DEFAULT 50,
    timer INT DEFAULT 30,   -- minutes
    FOREIGN KEY (module_id) REFERENCES Module(module_id) ON DELETE CASCADE
);

-- 12. Result
CREATE TABLE Result (
    result_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    test_id INT NOT NULL,
    score INT DEFAULT 0,
    judgment ENUM('pass','fail') DEFAULT 'fail',
    taken_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES User(user_id) ON DELETE CASCADE,
    FOREIGN KEY (test_id) REFERENCES Test(test_id) ON DELETE CASCADE
);

-- 13. Attempt
CREATE TABLE Attempt (
    attempt_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    question_id INT NOT NULL,
    selected_option ENUM('A','B','C','D'),
    is_correct TINYINT(1) DEFAULT 0,
    attempted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES User(user_id) ON DELETE CASCADE,
    FOREIGN KEY (question_id) REFERENCES Questions(question_id) ON DELETE CASCADE
);

-- 14. Certificates
CREATE TABLE Certificates (
    certificate_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    course_id INT NOT NULL,
    issue_date DATE DEFAULT (CURRENT_DATE),
    certificate_file VARCHAR(255),
    FOREIGN KEY (user_id) REFERENCES User(user_id) ON DELETE CASCADE,
    FOREIGN KEY (course_id) REFERENCES Course(course_id) ON DELETE CASCADE,
    UNIQUE KEY unique_cert (user_id, course_id)
);

-- 15. Feedback
CREATE TABLE Feedback (
    feedback_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    course_id INT NOT NULL,
    rating TINYINT CHECK (rating BETWEEN 1 AND 5),
    review TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES User(user_id) ON DELETE CASCADE,
    FOREIGN KEY (course_id) REFERENCES Course(course_id) ON DELETE CASCADE
);

-- ═══════════════════════════════════════
-- SEED DATA
-- ═══════════════════════════════════════
INSERT INTO Role (role_name) VALUES ('admin'),('student'),('instructor');
INSERT INTO Category (category_name) VALUES
('Web Development'),('Python'),('AI & ML'),('UI/UX Design'),
('Cyber Security'),('Data Science'),('Flutter'),('Java'),
('Digital Marketing'),('Graphic Design');

-- Admin user (password: admin123 hashed)
INSERT INTO User (full_name, email, password, role_id) VALUES
('Super Admin','admin@auralearn.com','$2b$12$hash_here',1);
