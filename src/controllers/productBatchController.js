const { db } = require("../../config/sequelize");
const response = require("../tools/response");
const { product_batch, documents } = db.lotnoOcr; // Destructure models

// Create Product Batch
exports.createProductBatch = async (req, res) => {
    try {
        const { document_id, top_text, bottom_text, is_verified } = req.body;
        if (document_id === undefined) {
             return response(req, res, { status: 400, message: "Document ID is required." });
        }
        // Optional: Check if document_id exists
        const parentDocument = await documents.findByPk(document_id);
        if (!parentDocument) {
             return response(req, res, { status: 404, message: "Associated document not found." });
        }

        const newBatch = await product_batch.create({ document_id, top_text, bottom_text, is_verified });
        response(req, res, { status: 201, data: newBatch, message: "Product batch created successfully." });
    } catch (error) {
        console.error("Create Product Batch Error:", error);
        response(req, res, { status: 500, message: "Failed to create product batch." });
    }
};

// Get All Product Batches (Optionally include Document info)
exports.getAllProductBatches = async (req, res) => {
    try {
        const batches = await product_batch.findAll({
            include: [{ model: documents, as: 'document', attributes: ['document_number', 'issued_date'] }]
        });
        response(req, res, { status: 200, data: batches });
    } catch (error) {
        console.error("Get All Product Batches Error:", error);
        response(req, res, { status: 500, message: "Failed to retrieve product batches." });
    }
};

// Get Product Batch by ID (Optionally include Document info)
exports.getProductBatchById = async (req, res) => {
    try {
        const { id } = req.params;
        const batch = await product_batch.findByPk(id, {
             include: [{ model: documents, as: 'document', attributes: ['document_number', 'issued_date'] }]
        });
        if (!batch) {
            return response(req, res, { status: 404, message: "Product batch not found." });
        }
        response(req, res, { status: 200, data: batch });
    } catch (error) {
        console.error("Get Product Batch By ID Error:", error);
        response(req, res, { status: 500, message: "Failed to retrieve product batch." });
    }
};

// Update Product Batch
exports.updateProductBatch = async (req, res) => {
    try {
        const { id } = req.params;
        const { document_id, top_text, bottom_text, is_verified } = req.body;

        const batch = await product_batch.findByPk(id);
        if (!batch) {
            return response(req, res, { status: 404, message: "Product batch not found." });
        }

        // Optional: Check if new document_id exists if changing
        if (document_id !== undefined && document_id !== batch.document_id) {
             const parentDocument = await documents.findByPk(document_id);
             if (!parentDocument) {
                  return response(req, res, { status: 404, message: "Associated document not found." });
             }
             batch.document_id = document_id;
        }
        if (top_text !== undefined) batch.top_text = top_text;
        if (bottom_text !== undefined) batch.bottom_text = bottom_text;
        if (is_verified !== undefined) batch.is_verified = is_verified;

        await batch.save();
        response(req, res, { status: 200, data: batch, message: "Product batch updated successfully." });
    } catch (error) {
        console.error("Update Product Batch Error:", error);
        response(req, res, { status: 500, message: "Failed to update product batch." });
    }
};

// Delete Product Batch
exports.deleteProductBatch = async (req, res) => {
    try {
        const { id } = req.params;
        const batch = await product_batch.findByPk(id);
        if (!batch) {
            return response(req, res, { status: 404, message: "Product batch not found." });
        }

        await batch.destroy();
        response(req, res, { status: 200, message: "Product batch deleted successfully." });
    } catch (error) {
        console.error("Delete Product Batch Error:", error);
        response(req, res, { status: 500, message: "Failed to delete product batch." });
    }
};