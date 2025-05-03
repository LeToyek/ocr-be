const path = require('path');
const multer = require('multer');
const fs = require('fs');
const response = require("../tools/response"); // Assuming you have a standard response tool
const runCommand = require('../tools/processUtils'); // Import the command runner

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

        // Define the path to the Python script relative to the project root or using absolute path
        const scriptPath = path.resolve(__dirname, '..', '..', 'final_app', 'main.py');

        // Prepare arguments for the Python script
        const scriptArgs = [
            scriptPath, // The script to run
            '--image-path',
            uploadedFilePath // Pass the absolute path of the uploaded file
            // Add other arguments like --output-excel if needed, e.g.:
            // '--output-excel',
            // path.resolve(__dirname, '..', '..', 'output', `${req.file.filename}.xlsx`)
        ];

        try {
            console.log(`Running Python script: ${scriptArgs.join(' ')}`);
            const scriptOutput = await runCommand(scriptArgs); // Await the promise
            console.log("Python script raw output:", scriptOutput); // Log the raw output

            // Attempt to parse the specific output format
            let parsedOutput;
            const resultPrefix = "Final Result: ";
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

                        parsedOutput = JSON.parse(jsonString);
                        console.log("Parsed Python script output:", parsedOutput);
                    } else {
                        throw new Error("Could not find valid dictionary braces {} in the script output after prefix.");
                    }
                } else {
                     // Fallback or handle as plain text if prefix not found
                    parsedOutput = { raw_output: scriptOutput };
                    console.warn(`Python script output did not contain the prefix "${resultPrefix}".`);
                }
            } catch (parseError) {
                console.error("Failed to parse Python script output:", parseError);
                // Send raw output if parsing fails
                parsedOutput = { raw_output: scriptOutput, parse_error: parseError.message };
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
                    scan_result: parsedOutput // Include the parsed output
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