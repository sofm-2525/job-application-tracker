
DROP DATABASE IF EXISTS job_tracker;
CREATE DATABASE job_tracker;
USE job_tracker;

-- ---------------------------
-- companies
-- ---------------------------
CREATE TABLE companies (
    company_id   INT PRIMARY KEY AUTO_INCREMENT,
    company_name VARCHAR(100) NOT NULL,
    industry     VARCHAR(50),
    website      VARCHAR(200),
    city         VARCHAR(50),
    state        VARCHAR(50),
    notes        TEXT
);

-- ---------------------------
-- jobs
-- requirements = JSON array of skills, e.g. ["Python", "SQL"]
-- ---------------------------
CREATE TABLE jobs (
    job_id       INT PRIMARY KEY AUTO_INCREMENT,
    company_id   INT,
    job_title    VARCHAR(100) NOT NULL,
    job_type     ENUM('Full-time', 'Part-time', 'Contract', 'Internship'),
    salary_min   INT,
    salary_max   INT,
    job_url      VARCHAR(300),
    date_posted  DATE,
    requirements JSON,
    FOREIGN KEY (company_id) REFERENCES companies(company_id) ON DELETE CASCADE
);

-- ---------------------------
-- applications
-- interview_data = JSON object, e.g. {"round": 1, "type": "Phone", ...}
-- ---------------------------
CREATE TABLE applications (
    application_id    INT PRIMARY KEY AUTO_INCREMENT,
    job_id            INT,
    application_date  DATE NOT NULL,
    status            ENUM('Applied', 'Screening', 'Interview', 'Offer', 'Rejected', 'Withdrawn') DEFAULT 'Applied',
    resume_version    VARCHAR(50),
    cover_letter_sent BOOLEAN DEFAULT FALSE,
    interview_data    JSON,
    FOREIGN KEY (job_id) REFERENCES jobs(job_id) ON DELETE CASCADE
);

-- ---------------------------
-- contacts
-- ---------------------------
CREATE TABLE contacts (
    contact_id   INT PRIMARY KEY AUTO_INCREMENT,
    company_id   INT,
    contact_name VARCHAR(100) NOT NULL,
    title        VARCHAR(100),
    email        VARCHAR(100),
    phone        VARCHAR(20),
    linkedin_url VARCHAR(200),
    notes        TEXT,
    FOREIGN KEY (company_id) REFERENCES companies(company_id) ON DELETE CASCADE
);

-- =====================================================
-- Sample data
-- =====================================================

INSERT INTO companies (company_name, industry, website, city, state, notes) VALUES
('Tech Solutions Inc',  'Technology',      'www.techsolutions.com',      'Miami',         'Florida',       'Fast-growing startup'),
('Data Analytics Corp', 'Data Science',    'www.dataanalytics.com',      'Austin',        'Texas',         NULL),
('Cloud Systems LLC',   'Cloud Computing', 'www.cloudsystems.com',       'Seattle',       'Washington',    'Hybrid work options'),
('Digital Innovations', 'Software',        'www.digitalinnovations.com', 'San Francisco', 'California',    NULL),
('Smart Tech Group',    'AI/ML',           'www.smarttech.com',          'Boston',        'Massachusetts', 'Strong mentorship program');

INSERT INTO jobs (company_id, job_title, job_type, salary_min, salary_max, job_url, date_posted, requirements) VALUES
(1, 'Software Developer',     'Full-time',  70000,  90000, 'https://www.techsolutions.com/careers/1',      '2025-01-15', '["Python", "SQL", "Flask"]'),
(1, 'Database Administrator', 'Full-time',  75000,  95000, 'https://www.techsolutions.com/careers/2',      '2025-01-10', '["SQL", "MySQL", "Linux", "Backup and Recovery"]'),
(2, 'Data Analyst',           'Full-time',  65000,  85000, 'https://www.dataanalytics.com/jobs/3',         '2025-01-12', '["Python", "SQL", "Tableau"]'),
(2, 'Intern - Data',          'Internship', 30000,  40000, 'https://www.dataanalytics.com/jobs/4',         '2025-01-13', '["Python", "Excel"]'),
(3, 'Cloud Engineer',         'Full-time',  80000, 100000, 'https://www.cloudsystems.com/jobs/5',          '2025-01-08', '["AWS", "Linux", "Python", "Docker"]'),
(4, 'Junior Developer',       'Full-time',  55000,  70000, 'https://www.digitalinnovations.com/jobs/6',    '2025-01-14', '["JavaScript", "HTML", "CSS", "Git"]'),
(4, 'Senior Developer',       'Full-time',  95000, 120000, 'https://www.digitalinnovations.com/jobs/7',    '2025-01-14', '["Java", "SQL", "Spring", "Git", "AWS"]'),
(4, 'Technical Writer',       'Contract',   55000,  75000, 'https://www.digitalinnovations.com/jobs/8',    '2025-01-12', '["Writing", "Markdown", "Git"]'),
(5, 'ML Engineer',            'Full-time',  90000, 115000, 'https://www.smarttech.com/careers/9',          '2025-01-11', '["Python", "Machine Learning", "SQL", "TensorFlow"]'),
(5, 'Part-time QA Tester',    'Part-time',  25000,  35000, 'https://www.smarttech.com/careers/10',         '2025-01-09', '["Testing", "Python", "Attention to Detail"]');

INSERT INTO applications (job_id, application_date, status, resume_version, cover_letter_sent, interview_data) VALUES
(1, '2025-01-16', 'Interview', 'v2.0', TRUE,
    '{"round": 1, "type": "Video", "date": "2025-01-24", "interviewer": "Maria Lopez", "notes": "Asked about SQL joins and Flask"}'),
(3, '2025-01-17', 'Screening', 'v2.0', FALSE, NULL),
(5, '2025-01-18', 'Applied',   'v1.0', TRUE,  NULL),
(7, '2025-01-19', 'Rejected',  'v1.0', FALSE, NULL),
(9, '2025-01-20', 'Offer',     'v3.0', TRUE,
    '{"round": 2, "type": "Onsite", "date": "2025-02-03", "interviewer": "James Chen", "notes": "Final round with the team lead"}');

INSERT INTO contacts (company_id, contact_name, title, email, phone, linkedin_url, notes) VALUES
(1, 'Maria Lopez',   'Engineering Manager', 'mlopez@techsolutions.com',     '305-555-0101', 'https://www.linkedin.com/in/example-mlopez',  'Interviewed me for Software Developer'),
(2, 'David Park',    'Recruiter',           'dpark@dataanalytics.com',      '512-555-0102', NULL,                                          'Reached out on LinkedIn'),
(4, 'Robert Kim',    'Engineering Manager', 'rkim@digitalinnovations.com',  NULL,           NULL,                                          NULL),
(5, 'James Chen',    'Team Lead',           'jchen@smarttech.com',          '617-555-0104', 'https://www.linkedin.com/in/example-jchen',   'Very friendly, follow up after offer');

-- Quick check: each table should show rows
SELECT 'companies' AS table_name, COUNT(*) AS row_count FROM companies
UNION ALL SELECT 'jobs', COUNT(*) FROM jobs
UNION ALL SELECT 'applications', COUNT(*) FROM applications
UNION ALL SELECT 'contacts', COUNT(*) FROM contacts;
