'use strict';

const express = require('express');
const router = express.Router();
const controller = require('../controllers/ocrResultController');
const { verifyToken } = require('../middlewares/authMiddleware');

router.use(verifyToken()); // Protect all OCR result routes

router.post('/', controller.createOcrResult);
router.get('/', controller.getAllOcrResults);
router.get('/:id', controller.getOcrResultById);
router.put('/:id', controller.updateOcrResult);
router.delete('/:id', controller.deleteOcrResult);

module.exports = router;