'use strict';

const express = require('express');
const router = express.Router();
const controller = require('../controllers/productBatchController');
const { verifyToken } = require('../middlewares/authMiddleware');

router.use(verifyToken()); // Protect all product batch routes

router.post('/', controller.createProductBatch);
router.get('/', controller.getAllProductBatches);
router.get('/available', controller.getAvailableProductBatches);
router.get('/:id', controller.getProductBatchById);
router.put('/:id', controller.updateProductBatch);
router.delete('/:id', controller.deleteProductBatch);
router.post('/with-document', controller.createProductBatchWithDocument);

module.exports = router;