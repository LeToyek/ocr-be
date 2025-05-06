const { db } = require("../../config/sequelize");
const response = require("../tools/response");
const { ocr_results, aio_employee, product_batch } = db.lotnoOcr; // Destructure models

// Create OCR Result
exports.createOcrResult = async (req, res) => {
    try {
        // employee_id might come from logged-in user (req.user.id) instead of body
        const employee_id = req.user.lg_nik; // Assuming verifyToken adds user info to req
        const { product_batch_id, top_text, bottom_text } = req.body;

        if (!employee_id || product_batch_id === undefined) {
             return response(req, res, { status: 400, message: "Employee ID and Product Batch ID are required." });
        }
        // Optional: Check if employee_id and product_batch_id exist
        const employee = await aio_employee.findByPk(employee_id);
        const batch = await product_batch.findByPk(product_batch_id);
        if (!employee) return response(req, res, { status: 404, message: "Associated employee not found." });
        if (!batch) return response(req, res, { status: 404, message: "Associated product batch not found." });


        const newResult = await ocr_results.create({
            employee_id,
            product_batch_id,
            top_text,
            bottom_text,
            photo_url
        });
        response(req, res, { status: 201, data: newResult, message: "OCR result created successfully." });
    } catch (error) {
        console.error("Create OCR Result Error:", error);
        response(req, res, { status: 500, message: "Failed to create OCR result." });
    }
};

// Get All OCR Results (Include related data)
exports.getAllOcrResults = async (req, res) => {
    try {
        const results = await ocr_results.findAll({
            include: [
                { model: aio_employee, as: 'employee', attributes: ['lg_nik', 'lg_name'] },
                { model: product_batch, as: 'product_batch', attributes: ['id'] } // Add more batch details if needed
            ]
        });
        response(req, res, { status: 200, data: results });
    } catch (error) {
        console.error("Get All OCR Results Error:", error);
        response(req, res, { status: 500, message: "Failed to retrieve OCR results." });
    }
};

// Get OCR Result by ID (Include related data)
exports.getOcrResultById = async (req, res) => {
    try {
        const { id } = req.params;
        const result = await ocr_results.findByPk(id, {
             include: [
                { model: aio_employee, as: 'employee', attributes: ['lg_nik', 'lg_name'] },
                { model: product_batch, as: 'product_batch', attributes: ['id'] }
            ]
        });
        if (!result) {
            return response(req, res, { status: 404, message: "OCR result not found." });
        }
        response(req, res, { status: 200, data: result });
    } catch (error) {
        console.error("Get OCR Result By ID Error:", error);
        response(req, res, { status: 500, message: "Failed to retrieve OCR result." });
    }
};

// Update OCR Result
exports.updateOcrResult = async (req, res) => {
    try {
        const { id } = req.params;
        // Decide which fields are updatable. Maybe only similarities or text?
        const { top_text, bottom_text, top_similarity, bottom_similarity, product_batch_id /*, employee_id */ } = req.body;
        // Usually employee_id wouldn't be changed. product_batch_id might change?

        const result = await ocr_results.findByPk(id);
        if (!result) {
            return response(req, res, { status: 404, message: "OCR result not found." });
        }

        // Optional: Validate new product_batch_id if changed
        if (product_batch_id !== undefined && product_batch_id !== result.product_batch_id) {
             const batch = await product_batch.findByPk(product_batch_id);
             if (!batch) return response(req, res, { status: 404, message: "Associated product batch not found." });
             result.product_batch_id = product_batch_id;
        }

        if (top_text !== undefined) result.top_text = top_text;
        if (bottom_text !== undefined) result.bottom_text = bottom_text;
        if (top_similarity !== undefined) result.top_similarity = top_similarity;
        if (bottom_similarity !== undefined) result.bottom_similarity = bottom_similarity;

        await result.save();
        response(req, res, { status: 200, data: result, message: "OCR result updated successfully." });
    } catch (error) {
        console.error("Update OCR Result Error:", error);
        response(req, res, { status: 500, message: "Failed to update OCR result." });
    }
};

// Delete OCR Result
exports.deleteOcrResult = async (req, res) => {
    try {
        const { id } = req.params;
        const result = await ocr_results.findByPk(id);
        if (!result) {
            return response(req, res, { status: 404, message: "OCR result not found." });
        }

        await result.destroy();
        response(req, res, { status: 200, message: "OCR result deleted successfully." });
    } catch (error) {
        console.error("Delete OCR Result Error:", error);
        response(req, res, { status: 500, message: "Failed to delete OCR result." });
    }
};