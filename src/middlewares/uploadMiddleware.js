const multer = require('multer');
const path = require('path');
const fs = require('fs-extra');

// Define allowed file types
const allowedFileTypes = [
    'image/jpeg',
    'image/png',
    'application/pdf',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document', // Word
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' // Excel
];

// Define maximum file size (in bytes)
const maxFileSize = 10 * 1024 * 1024; // 10 MB

// Define storage with dynamic subdirectories and file size limit
const storage = multer.diskStorage({
    destination: (req, file, cb) => {
        const category = req.body.dir.replace(/[^a-zA-Z0-9.]/g, '_') || 'default'; // Default if not specified

        // Create the subdirectory path
        const subdirectory = path.join(__dirname, '../../uploads', category);

        // Use fs-extra to ensure the subdirectory exists
        fs.ensureDir(subdirectory)
            .then(() => {
                // Subdirectory created successfully or already exists
                cb(null, subdirectory);
            })
            .catch(err => {
                // Handle error
                cb(err);
            });
    },
    filename: (req, file, cb) => {
        // Sanitize the filename to avoid issues with special characters
        const safeFilename = file.originalname.replace(/[^a-zA-Z0-9.-]/g, '_');
        const fullFilename = Date.now() + '-' + safeFilename;

        console.log(`Saving file as: ${fullFilename}`);

        cb(null, fullFilename);
    },
});

// File type filter function
const fileFilter = (req, file, cb) => {
    if (allowedFileTypes.includes(file.mimetype)) {
        // Accept the file
        cb(null, true);
    } else {
        // Reject the file
        cb(new Error('Invalid file type. Only JPEG, PNG, PDF, DOCX and XLSX files are allowed.'));
    }
};

// Create a dynamic upload middleware function
const uploadMiddleware = (fieldName, method, maxFiles = 1) => {
    const upload = multer({
        storage,
        fileFilter,
        limits: {
            fileSize: maxFileSize,
        },
    });

    let multerUpload;

    if (method === 'single') {
        multerUpload = upload.single(fieldName);
    } else if (method === 'array') {
        multerUpload = upload.array(fieldName, maxFiles);
    } else {
        throw new Error('Invalid upload method. Use "single" or "array".');
    }

    // Middleware to handle file uploads and strip absolute paths
    return (req, res, next) => {
        multerUpload(req, res, (err) => {
            if (err) {
                return res.status(400).json({ error: err.message });
            }

            // Adjust file paths
            if (req.file) {
                const baseUploadDir = path.resolve(__dirname, '../../uploads');
                req.file.path = path.relative(baseUploadDir, req.file.path);
                req.file.path = path.join('uploads', req.file.path); // Ensure 'uploads' is part of the path
            }

            if (req.files) {
                const baseUploadDir = path.resolve(__dirname, '../../uploads');
                req.files.forEach(file => {
                    file.path = path.relative(baseUploadDir, file.path);
                    file.path = path.join('uploads', file.path); // Ensure 'uploads' is part of the path
                });
            }

            next();
        });
    };
};

module.exports = uploadMiddleware;