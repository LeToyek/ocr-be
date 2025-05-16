'use strict';

const express = require('express');
const router = express.Router();
const controller = require('../controllers/folderController');
const { verifyToken } = require('../middlewares/authMiddleware');

// router.use(verifyToken()); // Protect all OCR result routes

router.get('/', controller.getFolderContents);

module.exports = router;
