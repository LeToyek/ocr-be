'use strict';

const express = require('express');
const router = express.Router();
const controller = require('../controllers/verifyController');
const { verifyToken } = require('../middlewares/authMiddleware');

router.use(verifyToken()); // Protect all OCR result routes

router.post('/', controller.verifyOcrResult);

module.exports = router;
