'use strict';

const express = require('express');
const router = express.Router();
const controller = require('../controllers/categoryController');
const { verifyToken } = require('../middlewares/authMiddleware'); // Assuming middleware path

// Apply verifyToken middleware to all category routes
router.use(verifyToken());

router.post('/', controller.createCategory);
router.get('/', controller.getAllCategories);
router.get('/:id', controller.getCategoryById);
router.put('/:id', controller.updateCategory);
router.delete('/:id', controller.deleteCategory);

module.exports = router;