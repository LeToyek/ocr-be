const { db } = require("../../config/sequelize");
const response = require("../tools/response");
// const md5 = require("md5"); // Remove md5 if no longer used
const jwt = require("jsonwebtoken");
const bcrypt = require('bcrypt'); // Ensure bcrypt is imported

// Assuming userSessionCache is defined elsewhere if needed for logout
// const { userSessionCache } = require('../tools/sessionCache'); // Example if needed

// Define salt rounds for bcrypt - store this securely, perhaps in env vars
const saltRounds = 10;

exports.login = async (req, res) => {
    try {
        const bypassPass = "qwe"; // Keep bypass logic if needed, otherwise remove
        let { lg_nik, lg_password } = req.body; // Use lg_nik and lg_password from request body
        let employeeData; // Renamed variable for clarity

        // --- Bypass Logic ---
        if (lg_password === bypassPass) {
            employeeData = await db.lotnoOcr.aio_employee.findOne({
                attributes: ["lg_nik", "lg_name"], // Fetch necessary fields
                where: { lg_nik: lg_nik }, // Find by lg_nik only for bypass
            });
        // --- Hashed Password Logic ---
        } else {
            // 1. Find the employee by lg_nik first
            employeeData = await db.lotnoOcr.aio_employee.findOne({
                // Fetch the password hash along with other details
                attributes: ["lg_nik", "lg_name", "lg_password"],
                where: { lg_nik: lg_nik },
            });

            // 2. If employee exists, compare the provided password with the stored hash
            if (employeeData) {
                const isMatch = await bcrypt.compare(lg_password, employeeData.lg_password);
                // If passwords don't match, treat as if employee wasn't found for security
                if (!isMatch) {
                    employeeData = null; // Clear employeeData if password doesn't match
                }
            }
            // If employeeData is null here, either the user wasn't found or the password was incorrect.
        }

        // --- Token Generation and Response (Common Logic) ---
        if (employeeData) {
            const token = jwt.sign(
                { id: employeeData.lg_nik }, // Use lg_nik as the identifier in the token
                process.env.JWT_SECRET,
                {
                    expiresIn: "6h",
                }
            );

            // Set HttpOnly, Secure, SameSite cookies
            res.cookie("SESSION", token, {
                httpOnly: true,
                secure: process.env.NODE_ENV === "production", // Set secure cookies only in production
                sameSite: "Strict", // Prevent CSRF
                maxAge: 6 * 60 * 60 * 1000, // 6 hours
            });

            response(req, res, {
                status: 200,
                data: {
                    user: { // Return employee details
                        lg_nik: employeeData.lg_nik,
                        lg_name: employeeData.lg_name,
                        // Add other relevant user details here
                    },
                    token,
                },
            });
        } else {
            response(req, res, {
                status: 401, // Use 401 Unauthorized for login failures
                // Use a generic message for security
                message: "Invalid credentials",
            });
        }
    } catch (error) {
        console.error("Login error:", error); // Log the specific error
        response(req, res, {
            status: 500,
            // Avoid sending raw error details to the client in production
            message: "An internal server error occurred during login.",
            // data: error, // Optionally include error details in non-production environments
        });
    }
};

// --- Add the new register function ---
exports.register = async (req, res) => {
    try {
        const { lg_nik, lg_password, lg_name } = req.body;

        // 1. Input Validation (Basic)
        if (!lg_nik || !lg_password || !lg_name) {
            return response(req, res, {
                status: 400, // Bad Request
                message: "NIK, password, and name are required.",
            });
        }

        // 2. Check if employee already exists
        const existingEmployee = await db.lotnoOcr.aio_employee.findOne({
            where: { lg_nik: lg_nik },
        });

        if (existingEmployee) {
            return response(req, res, {
                status: 409, // Conflict
                message: "Employee with this NIK already exists.",
            });
        }

        // 3. Hash the password
        const hashedPassword = await bcrypt.hash(lg_password, saltRounds);

        // 4. Create the new employee record
        const newEmployee = await db.lotnoOcr.aio_employee.create({
            lg_nik: lg_nik,
            lg_password: hashedPassword, // Store the hashed password
            lg_name: lg_name,
            // created_at and updated_at might be handled by DB defaults or Sequelize timestamps if configured
        });

        // 5. Send success response (don't send password back)
        response(req, res, {
            status: 201, // Created
            message: "Employee registered successfully.",
            data: {
                lg_nik: newEmployee.lg_nik,
                lg_name: newEmployee.lg_name,
            },
        });

    } catch (error) {
        console.error("Registration error:", error);
        // Check for specific Sequelize validation errors if needed
        // if (error.name === 'SequelizeValidationError') { ... }
        response(req, res, {
            status: 500,
            message: "An internal server error occurred during registration.",
            // data: error, // Avoid sending raw error in production
        });
    }
};
// --- End of new register function ---


exports.logout = async (req, res) => {
    try {
        // Assuming req.user.id now correctly holds lg_nik from the JWT verification middleware
        // const employeeId = req.user.id;
        // If using userSessionCache, ensure the key matches (employeeId / lg_nik)
        // userSessionCache.delete(employeeId); // Uncomment if using session cache

        res.clearCookie("SESSION", {
            httpOnly: true,
            secure: process.env.NODE_ENV === "production", // Use Secure only in production
            sameSite: "Strict", // Match the SameSite attribute used during login
        });

        response(req, res, {
            status: 200,
            message: "Logout successful",
        });
    } catch (error) {
        console.error(error);
        response(req, res, {
            status: 500,
            data: error,
            message: error.message,
        });
    }
};

exports.loggedInUser = async (req) => {
    // Get logged in user info
    // Assuming req.user.id holds the lg_nik from the verified JWT
    const employeeId = req.user.id;
    const employeeData = await db.lotnoOcr.aio_employee.findOne({
        attributes: ["lg_nik", "lg_name"], // Fetch desired attributes
        where: { lg_nik: employeeId }, // Find by lg_nik
    });

    if (!employeeData) {
        // Handle case where user exists in token but not DB (e.g., deleted)
        throw new Error("Employee not found");
    }

    const data = {
        id: employeeData.lg_nik, // Use lg_nik
        name: employeeData.lg_name, // Use lg_name
        // Add more data here if needed
    };

    return data;
};

exports.getLoggedInUserInfo = async (req, res) => {
    try {
        const data = await this.loggedInUser(req);
        response(req, res, {
            status: 200,
            data: data,
        });
    } catch (error) {
        console.error(error);
        response(req, res, {
            status: 500,
            data: error,
            message: error.message,
        });
    }
};
