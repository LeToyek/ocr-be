const { db } = require("../../config/sequelize");
const response = require("../tools/response");
const { category } = db.lotnoOcr; // Destructure the category model

// Create Category
exports.createCategory = async (req, res) => {
    try {
        const { category_name } = req.body;
        if (!category_name) {
            return response(req, res, { status: 400, message: "Category name is required." });
        }
        // Add created_at and updated_at manually if not handled by Sequelize timestamps:true
        const newCategory = await category.create({
            category_name,
            created_at: new Date(),
            updated_at: new Date()
         });
        response(req, res, { status: 201, data: newCategory, message: "Category created successfully." });
    } catch (error) {
        console.error("Create Category Error:", error);
        response(req, res, { status: 500, message: "Failed to create category." });
    }
};

// Get All Categories
exports.getAllCategories = async (req, res) => {
    try {
        const categories = await category.findAll();
        response(req, res, { status: 200, data: categories });
    } catch (error) {
        console.error("Get All Categories Error:", error);
        response(req, res, { status: 500, message: "Failed to retrieve categories." });
    }
};

// Get Category by ID
exports.getCategoryById = async (req, res) => {
    try {
        const { id } = req.params;
        const foundCategory = await category.findByPk(id);
        if (!foundCategory) {
            return response(req, res, { status: 404, message: "Category not found." });
        }
        response(req, res, { status: 200, data: foundCategory });
    } catch (error) {
        console.error("Get Category By ID Error:", error);
        response(req, res, { status: 500, message: "Failed to retrieve category." });
    }
};

// Update Category
exports.updateCategory = async (req, res) => {
    try {
        const { id } = req.params;
        const { category_name } = req.body;

        const foundCategory = await category.findByPk(id);
        if (!foundCategory) {
            return response(req, res, { status: 404, message: "Category not found." });
        }

        if (category_name !== undefined) { // Only update if provided
            foundCategory.category_name = category_name;
            foundCategory.updated_at = new Date(); // Update timestamp manually
        }

        await foundCategory.save();
        response(req, res, { status: 200, data: foundCategory, message: "Category updated successfully." });
    } catch (error) {
        console.error("Update Category Error:", error);
        response(req, res, { status: 500, message: "Failed to update category." });
    }
};

// Delete Category
exports.deleteCategory = async (req, res) => {
    try {
        const { id } = req.params;
        const foundCategory = await category.findByPk(id);
        if (!foundCategory) {
            return response(req, res, { status: 404, message: "Category not found." });
        }

        await foundCategory.destroy();
        response(req, res, { status: 200, message: "Category deleted successfully." }); // Or 204 No Content
    } catch (error) {
        console.error("Delete Category Error:", error);
        // Handle potential foreign key constraint errors if needed
        response(req, res, { status: 500, message: "Failed to delete category." });
    }
};