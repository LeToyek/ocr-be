'use strict';

const express = require('express');
const router = express.Router();
const controller = require('../controllers/employeeController');
const { verifyToken } = require('../middlewares/authMiddleware');

// Apply token verification. Consider adding role checks for sensitive operations.
router.use(verifyToken());

// Note: POST / might conflict with /register in authRoutes if both are mounted at the same base path (e.g., /api/employees vs /api/auth)
// Consider if this endpoint is needed or if registration handles creation.
// If needed, ensure only authorized users (e.g., admins) can access it.
router.post('/', controller.createEmployee); // Requires authorization check

router.get('/', controller.getAllEmployees); // Get all employees
router.get('/:lg_nik', controller.getEmployeeById); // Get specific employee by NIK
router.put('/:lg_nik', controller.updateEmployee); // Update specific employee
router.delete('/:lg_nik', controller.deleteEmployee); // Delete specific employee (Requires authorization check)

module.exports = router;