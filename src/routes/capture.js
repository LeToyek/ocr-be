'use strict';

const express = require('express');
const router = express.Router();
const controller = require('../controllers/captureController');
const { verifyToken } = require('../middlewares/authMiddleware'); // Assuming middleware path

// Define the route for uploading a photo
// POST /api/capture/upload
// The verifyToken middleware runs first to ensure the user is authenticated.
// The controller.uploadPhoto function handles the multer middleware internally.
router.post('/', verifyToken(), controller.scanPhoto);
router.post('/test', verifyToken(), controller.scanPhotoTest);


module.exports = router;