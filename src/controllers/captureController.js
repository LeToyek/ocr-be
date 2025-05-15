const path = require('path');
const multer = require('multer');
const fs = require('fs');
const response = require("../tools/response"); // Assuming you have a standard response tool
const runCommand = require('../tools/processUtils'); // Import the command runner
const { db } = require("../../config/sequelize");
const { ocr_results, aio_employee, product_batch } = db.lotnoOcr; // Destructure models

// Define the destination directory using path.join
// __dirname will be d:\SKRIPSI\CODE\ocr-be\src\controllers
// We need to go up two levels to reach d:\SKRIPSI\CODE\ocr-be\
const uploadDir = path.join(__dirname, '..', '..', 'public');

// Ensure the upload directory exists
if (!fs.existsSync(uploadDir)) {
    fs.mkdirSync(uploadDir, { recursive: true });
    console.log(`Created directory: ${uploadDir}`);
} else {
    console.log(`Upload directory already exists: ${uploadDir}`);
}


// Configure Multer storage
const storage = multer.diskStorage({
    destination: function (req, file, cb) {
        cb(null, uploadDir); // Use the calculated absolute path
    },
    filename: function (req, file, cb) {
        // Create a unique filename (e.g., timestamp-originalname)
        const uniqueSuffix = Date.now() + '-' + Math.round(Math.random() * 1E9);
        const extension = path.extname(file.originalname);
        cb(null, file.fieldname + '-' + uniqueSuffix + extension);
    }
});

// Configure Multer upload middleware
// You might want to add file filters (e.g., only allow images)
const upload = multer({
    storage: storage,
    limits: { fileSize: 10 * 1024 * 1024 }, // Example: Limit file size to 10MB
    fileFilter: function (req, file, cb) {
        // Accept images only
        if (!file.originalname.match(/\.(jpg|jpeg|png|gif)$/i)) {
            req.fileValidationError = 'Only image files (jpg, jpeg, png, gif) are allowed!';
            // Reject file
            return cb(null, false);
            // Or pass an error: return cb(new Error('Only image files are allowed!'), false);
        }
        // Accept file
        cb(null, true);
    }
}).single('photo'); // 'photo' is the field name in the form-data request

// Controller function to handle the upload request and trigger scan
exports.scanPhoto = (req, res) => {
    // Use the 'upload' middleware first
    upload(req, res, async function (err) { // Make the callback async
        // Handle Multer errors
        if (err instanceof multer.MulterError) {
            console.error("Multer error:", err);
            return response(req, res, { status: 400, message: `Multer error: ${err.message}` });
        } else if (err) {
            // Handle other errors (like file filter rejection if error passed in cb)
            console.error("Upload error:", err);
            return response(req, res, { status: 500, message: `Upload error: ${err.message || 'Unknown error'}` });
        }

        // Handle file filter validation error (if set on req)
        if (req.fileValidationError) {
             return response(req, res, { status: 400, message: req.fileValidationError });
        }

        // Check if a file was actually uploaded
        if (!req.file) {
            return response(req, res, { status: 400, message: 'No photo file was uploaded.' });
        }

        // File uploaded successfully, now run the Python script
        console.log('File uploaded successfully:', req.file);
        const uploadedFilePath = req.file.path; // Absolute path from multer
        const uploadedFilename = req.file.filename; // Get the generated filename

        // Define the path to the Python script relative to the project root or using absolute path
        const scriptPath = path.resolve(__dirname, '..', '..', 'final_app', 'main.py');

        // Prepare arguments for the Python script
        const scriptArgs = [
            scriptPath, // The script to run
            '--image-path',
            uploadedFilePath // Pass the absolute path of the uploaded file
        ];

        try {
            console.log(`Running Python script: ${scriptArgs.join(' ')}`);
            const scriptOutput = await runCommand(scriptArgs); // Await the promise
            console.log("Python script raw output:", scriptOutput); // Log the raw output

            // Attempt to parse the specific output format
            let parsedOutput;
            const resultPrefix = "Processing Result: ";
            try {
                // Find the start of the dictionary after the prefix
                const dictStartIndex = scriptOutput.indexOf(resultPrefix);

                if (dictStartIndex !== -1) {
                    // Extract the string starting from '{' after the prefix
                    const jsonLikeStringStartIndex = scriptOutput.indexOf('{', dictStartIndex + resultPrefix.length);
                    const jsonLikeStringEndIndex = scriptOutput.lastIndexOf('}');

                    if (jsonLikeStringStartIndex !== -1 && jsonLikeStringEndIndex !== -1 && jsonLikeStringEndIndex > jsonLikeStringStartIndex) {
                        let jsonLikeString = scriptOutput.substring(jsonLikeStringStartIndex, jsonLikeStringEndIndex + 1);

                        // Replace single quotes with double quotes for valid JSON
                        // Be careful not to replace single quotes within string values if they exist
                        // A safer approach might involve more complex regex or specific handling if needed
                        // This simple replace works if keys and string values don't contain single quotes themselves
                        const jsonString = jsonLikeString.replace(/'/g, '"');
                        console.log("jsonString : ", jsonString);
                        

                        parsedOutput = JSON.parse(jsonString);
                        console.log("Parsed Python script output:", parsedOutput);
                    } else {
                        throw new Error("Could not find valid dictionary braces {} in the script output after prefix.");
                    }
                } else {
                    parsedOutput = { raw_output: scriptOutput }; // Keep raw output if prefix not found
                    console.warn(`Python script output did not contain the prefix "${resultPrefix}".`);
                    // Decide if you want to proceed without parsed data or return an error
                    // For now, we'll let it proceed, but the DB insert might fail or be incomplete
                }
            } catch (parseError) {
                console.error("Failed to parse Python script output:", parseError);
                parsedOutput = { raw_output: scriptOutput, parse_error: parseError.message };
                // Decide if you want to proceed or return an error
                // For now, we'll let it proceed, but the DB insert might fail or be incomplete
            }

            // --- Create ocr_results record ---
            let newResult = null;
            // Ensure we have the necessary parsed data and IDs before attempting to create
            // Check if parsedOutput has the required fields and status is success (optional)
            if (parsedOutput && parsedOutput.formatted_top && parsedOutput.formatted_bottom) {
                try {
                    // --- IMPORTANT: Get employee_id and product_batch_id ---
                    // Adjust req.user.lg_nik based on your actual auth middleware structure
                    const employee_id = '1133'

                    if (!employee_id) {
                        throw new Error("Employee ID not found in request. User might not be authenticated.");
                    }

                    const top_text = parsedOutput.formatted_top;
                    const bottom_text = parsedOutput.formatted_bottom;
                    const status = parsedOutput.status
                    const category = parsedOutput.category
                    // Construct a relative URL path assuming 'public' is served statically
                    const photo_url = `/public/${uploadedFilename}`;

                    console.log("Creating ocr_results record with data:", {
                        employee_id,
                        top_text,
                        bottom_text,
                        photo_url
                    });

                    newResult = await ocr_results.create({
                        employee_id,
                        top_text,
                        bottom_text,
                        photo_url,
                        category,
                        status,
                        created_at: new Date(), // Sequelize might handle this if timestamps: true
                        updated_at: new Date()  // Sequelize might handle this if timestamps: true
                    });
                    parsedOutput.id = newResult.id; // Add ID to response data

                    console.log("ocr_results record created successfully:", newResult.id);

                } catch (dbError) {
                    console.error("Failed to create ocr_results record:", dbError);
                    // Decide how to handle DB error:
                    // Option 1: Return specific DB error response
                    return response(req, res, {
                        status: 500,
                        message: "Photo scanned, but failed to save result to database.",
                        error: dbError.message || "Database error",
                        upload_info: { filename: uploadedFilename, path: uploadedFilePath },
                        scan_result: parsedOutput // Still include scan result if available
                    });
                    // Option 2: Continue and just log the error (less ideal)
                    // parsedOutput.db_error = dbError.message; // Add error info to response data
                }
            } else {
                console.warn("Skipping database insert due to missing parsed data or non-success status.");
                // Optionally add a note to the parsedOutput that DB insert was skipped
                if (parsedOutput) {
                    parsedOutput.db_insert_skipped = true;
                    parsedOutput.db_insert_skip_reason = "Missing required data or non-success status from OCR.";
                }
            }
            // --- End Create ocr_results record ---


            // Send success response including upload info, script result, and DB result (if created)
            response(req, res, {
                status: 200,
                message: "Photo uploaded and scanned successfully!",
                data: {
                    upload_info: {
                        filename: uploadedFilename, // Use the stored filename
                        originalname: req.file.originalname,
                        path: uploadedFilePath,
                        size: req.file.size
                    },
                    scan_result: parsedOutput, // Include the parsed output (might have error flags)
                    database_result: newResult // Include the created record (or null)
                }
            });

        } catch (scriptError) {
            console.error("Python script execution failed:", scriptError);
            // Send error response, but acknowledge upload was successful
            response(req, res, {
                status: 500,
                message: "Photo uploaded, but scanning failed.",
                error: scriptError.message || "Unknown error during script execution.",
                upload_info: { // Still provide upload info
                    filename: req.file.filename,
                    path: uploadedFilePath
                }
            });
        }
    });
};

exports.scanPhotoTest = (req, res) => {

    upload(req, res, async function (err) { // Make the callback async
        // Handle Multer errors
        if (err instanceof multer.MulterError) {
            console.error("Multer error:", err);
            return response(req, res, { status: 400, message: `Multer error: ${err.message}` });
        } else if (err) {
            // Handle other errors (like file filter rejection if error passed in cb)
            console.error("Upload error:", err);
            return response(req, res, { status: 500, message: `Upload error: ${err.message || 'Unknown error'}` });
        }

        // Handle file filter validation error (if set on req)
        if (req.fileValidationError) {
             return response(req, res, { status: 400, message: req.fileValidationError });
        }

        // Check if a file was actually uploaded
        if (!req.file) {
            return response(req, res, { status: 400, message: 'No photo file was uploaded.' });
        }

        // File uploaded successfully, now run the Python script
        console.log('File uploaded successfully:', req.file);
        const uploadedFilePath = req.file.path; // Absolute path from multer
        const uploadedFilename = req.file.filename; // Get the generated filename

        try {
            // --- Create ocr_results record ---
            const parsedOutput = {
                "status": "success",
                "message": "Valid Lokal format",
                "formatted_top": "28.09.24 K2",
                "formatted_bottom": "04:22",
                "category": "CAP"
            }
            let newResult = null;
            // Ensure we have the necessary parsed data and IDs before attempting to create
            // Check if parsedOutput has the required fields and status is success (optional)
            if (parsedOutput && parsedOutput.formatted_top && parsedOutput.formatted_bottom) {
                try {
                    // --- IMPORTANT: Get employee_id and product_batch_id ---
                    // Adjust req.user.lg_nik based on your actual auth middleware structure
                    const employee_id = req.user?.id;
                    console.log("REQ USERRR : ", req.user)
                    console.log("employee_id: ", employee_id)

                    if (!employee_id) {
                        throw new Error("Employee ID not found in request. User might not be authenticated.");
                    }

                    const top_text = parsedOutput.formatted_top;
                    const bottom_text = parsedOutput.formatted_bottom;
                    const status = parsedOutput.status
                    const category = parsedOutput.category
                    // Construct a relative URL path assuming 'public' is served statically
                    const photo_url = `/public/${uploadedFilename}`;

                    console.log("Creating ocr_results record with data:", {
                        employee_id,
                        top_text,
                        bottom_text,
                        photo_url
                    });

                    newResult = await ocr_results.create({
                        employee_id,
                        top_text,
                        bottom_text,
                        photo_url,
                        category,
                        status,
                        created_at: new Date(), // Sequelize might handle this if timestamps: true
                        updated_at: new Date()  // Sequelize might handle this if timestamps: true
                    });
                    
                    parsedOutput.id = newResult.id; // Add ID to response data

                    console.log("ocr_results record created successfully:", newResult.id);

                } catch (dbError) {
                    console.error("Failed to create ocr_results record:", dbError);
                    // Decide how to handle DB error:
                    // Option 1: Return specific DB error response
                    return response(req, res, {
                        status: 500,
                        message: "Photo scanned, but failed to save result to database.",
                        error: dbError.message || "Database error",
                        upload_info: { filename: uploadedFilename, path: uploadedFilePath },
                        scan_result: parsedOutput // Still include scan result if available
                    });
                    // Option 2: Continue and just log the error (less ideal)
                    // parsedOutput.db_error = dbError.message; // Add error info to response data
                }
            }else {
                console.warn("Skipping database insert due to missing parsed data or non-success status.");
                // Optionally add a note to the parsedOutput that DB insert was skipped
                if (parsedOutput) {
                    parsedOutput.db_insert_skipped = true;
                    parsedOutput.db_insert_skip_reason = "Missing required data or non-success status from OCR.";
                }
            }
            

            // Send success response including upload info and script result
            response(req, res, {
                status: 200,
                message: "Photo uploaded and scanned successfully!",
                data: {
                    upload_info: {
                        filename: req.file.filename,
                        originalname: req.file.originalname,
                        path: uploadedFilePath,
                        size: req.file.size
                    },
                    scan_result: parsedOutput, // Include the parsed output (might have error flags),
                    database_result: newResult
                }
            });

        } catch (scriptError) {
            console.error("Python script execution failed:", scriptError);
            // Send error response, but acknowledge upload was successful
            response(req, res, {
                status: 500,
                message: "Photo uploaded, but scanning failed.",
                error: scriptError.message || "Unknown error during script execution.",
                upload_info: { // Still provide upload info
                    filename: req.file.filename,
                    path: uploadedFilePath
                }
            });
        }
    });
};