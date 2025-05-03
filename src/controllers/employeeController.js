const { db } = require("../../config/sequelize");
const response = require("../tools/response");
const bcrypt = require('bcrypt');
const { aio_employee } = db.lotnoOcr;

const saltRounds = 10; // Same as in authController

// Create Employee (Consider security implications vs. register)
exports.createEmployee = async (req, res) => {
    // This is very similar to register. Ensure proper authorization for this endpoint.
    try {
        const { lg_nik, lg_password, lg_name } = req.body;
        if (!lg_nik || !lg_password || !lg_name) {
            return response(req, res, { status: 400, message: "NIK, password, and name are required." });
        }
        const existingEmployee = await aio_employee.findByPk(lg_nik);
        if (existingEmployee) {
            return response(req, res, { status: 409, message: "Employee with this NIK already exists." });
        }
        const hashedPassword = await bcrypt.hash(lg_password, saltRounds);
        const newEmployee = await aio_employee.create({
            lg_nik,
            lg_password: hashedPassword,
            lg_name
        });
        // Exclude password from response
        const { lg_password: _, ...employeeData } = newEmployee.get({ plain: true });
        response(req, res, { status: 201, data: employeeData, message: "Employee created successfully." });
    } catch (error) {
        console.error("Create Employee Error:", error);
        response(req, res, { status: 500, message: "Failed to create employee." });
    }
};

// Get All Employees (Exclude passwords)
exports.getAllEmployees = async (req, res) => {
    try {
        const employees = await aio_employee.findAll({
            attributes: { exclude: ['lg_password'] } // Exclude password field
        });
        response(req, res, { status: 200, data: employees });
    } catch (error) {
        console.error("Get All Employees Error:", error);
        response(req, res, { status: 500, message: "Failed to retrieve employees." });
    }
};

// Get Employee by ID (Exclude password)
exports.getEmployeeById = async (req, res) => {
    try {
        const { lg_nik } = req.params; // Use lg_nik as the identifier
        const employee = await aio_employee.findByPk(lg_nik, {
             attributes: { exclude: ['lg_password'] }
        });
        if (!employee) {
            return response(req, res, { status: 404, message: "Employee not found." });
        }
        response(req, res, { status: 200, data: employee });
    } catch (error) {
        console.error("Get Employee By ID Error:", error);
        response(req, res, { status: 500, message: "Failed to retrieve employee." });
    }
};

// Update Employee
exports.updateEmployee = async (req, res) => {
    try {
        const { lg_nik } = req.params;
        const { lg_name, lg_password } = req.body; // Allow updating name and password

        const employee = await aio_employee.findByPk(lg_nik);
        if (!employee) {
            return response(req, res, { status: 404, message: "Employee not found." });
        }

        // Update name if provided
        if (lg_name !== undefined) {
            employee.lg_name = lg_name;
        }

        // Update password if provided
        if (lg_password) {
            employee.lg_password = await bcrypt.hash(lg_password, saltRounds);
        }

        await employee.save();

        // Exclude password from response
        const { lg_password: _, ...employeeData } = employee.get({ plain: true });
        response(req, res, { status: 200, data: employeeData, message: "Employee updated successfully." });
    } catch (error) {
        console.error("Update Employee Error:", error);
        response(req, res, { status: 500, message: "Failed to update employee." });
    }
};

// Delete Employee
exports.deleteEmployee = async (req, res) => {
    try {
        const { lg_nik } = req.params;
        const employee = await aio_employee.findByPk(lg_nik);
        if (!employee) {
            return response(req, res, { status: 404, message: "Employee not found." });
        }

        // Add checks here: prevent self-deletion? Admin only?
        // if (req.user.id === lg_nik) {
        //     return response(req, res, { status: 403, message: "Cannot delete yourself." });
        // }

        await employee.destroy();
        response(req, res, { status: 200, message: "Employee deleted successfully." });
    } catch (error) {
        console.error("Delete Employee Error:", error);
        response(req, res, { status: 500, message: "Failed to delete employee." });
    }
};