'use strict';

const express = require('express');
const router = express.Router();
const controller = require('../controllers/authController');
const { verifyToken } = require('../middlewares/authMiddleware');

router.post('/login', controller.login);
router.post('/logout', verifyToken(), controller.logout);
router.get('/info', verifyToken(), controller.getLoggedInUserInfo);

module.exports = router;