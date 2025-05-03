const { db } = require("../../config/sequelize");
const response = require("../tools/response");
const { documents, category } = db.lotnoOcr; // Destructure models

// Create Document
exports.createDocument = async (req, res) => {
    try {
        const { category_id, document_number, issued_date } = req.body;
        // Basic validation
        if (category_id === undefined || !document_number || !issued_date) {
            return response(req, res, { status: 400, message: "Category ID, document number, and issued date are required." });
        }
        // Optional: Check if category_id exists
        const parentCategory = await category.findByPk(category_id);
        if (!parentCategory) {
             return response(req, res, { status: 404, message: "Associated category not found." });
        }

        const newDocument = await documents.create({ category_id, document_number, issued_date });
        response(req, res, { status: 201, data: newDocument, message: "Document created successfully." });
    } catch (error) {
        console.error("Create Document Error:", error);
        response(req, res, { status: 500, message: "Failed to create document." });
    }
};

// Get All Documents (Optionally include Category info)
exports.getAllDocuments = async (req, res) => {
    try {
        const allDocuments = await documents.findAll({
            include: [{ model: category, as: 'category', attributes: ['category_name'] }] // Include associated category name
        });
        response(req, res, { status: 200, data: allDocuments });
    } catch (error) {
        console.error("Get All Documents Error:", error);
        response(req, res, { status: 500, message: "Failed to retrieve documents." });
    }
};

// Get Document by ID (Optionally include Category info)
exports.getDocumentById = async (req, res) => {
    try {
        const { id } = req.params;
        const foundDocument = await documents.findByPk(id, {
             include: [{ model: category, as: 'category', attributes: ['category_name'] }]
        });
        if (!foundDocument) {
            return response(req, res, { status: 404, message: "Document not found." });
        }
        response(req, res, { status: 200, data: foundDocument });
    } catch (error) {
        console.error("Get Document By ID Error:", error);
        response(req, res, { status: 500, message: "Failed to retrieve document." });
    }
};

// Update Document
exports.updateDocument = async (req, res) => {
    try {
        const { id } = req.params;
        const { category_id, document_number, issued_date } = req.body;

        const foundDocument = await documents.findByPk(id);
        if (!foundDocument) {
            return response(req, res, { status: 404, message: "Document not found." });
        }

        // Optional: Check if new category_id exists if it's being changed
        if (category_id !== undefined && category_id !== foundDocument.category_id) {
             const parentCategory = await category.findByPk(category_id);
             if (!parentCategory) {
                  return response(req, res, { status: 404, message: "Associated category not found." });
             }
             foundDocument.category_id = category_id;
        }
        if (document_number !== undefined) foundDocument.document_number = document_number;
        if (issued_date !== undefined) foundDocument.issued_date = issued_date;

        await foundDocument.save();
        response(req, res, { status: 200, data: foundDocument, message: "Document updated successfully." });
    } catch (error) {
        console.error("Update Document Error:", error);
        response(req, res, { status: 500, message: "Failed to update document." });
    }
};

// Delete Document
exports.deleteDocument = async (req, res) => {
    try {
        const { id } = req.params;
        const foundDocument = await documents.findByPk(id);
        if (!foundDocument) {
            return response(req, res, { status: 404, message: "Document not found." });
        }

        await foundDocument.destroy();
        response(req, res, { status: 200, message: "Document deleted successfully." });
    } catch (error) {
        console.error("Delete Document Error:", error);
        response(req, res, { status: 500, message: "Failed to delete document." });
    }
};