'use strict';

const express = require('express');
const router = express.Router();
const controller = require('../controllers/documentController');
const { verifyToken } = require('../middlewares/authMiddleware');

router.use(verifyToken()); // Protect all document routes

router.post('/', controller.createDocument);
router.get('/', controller.getAllDocuments);
router.get('/:id', controller.getDocumentById);
router.put('/:id', controller.updateDocument);
router.delete('/:id', controller.deleteDocument);

module.exports = router;