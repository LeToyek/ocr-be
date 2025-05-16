const path = require('path');
const fs = require('fs').promises;
const response = require("../tools/response");

exports.getFolderContents = async (req, res) => {
    try {
        // Define the base directory (public folder where images are stored)
        const baseDir = path.join(__dirname, '..', '..', 'public');
        
        // Get all items in the directory
        const items = await fs.readdir(baseDir, { withFileTypes: true });
        
        // Process each item
        const contents = await Promise.all(items.map(async (item) => {
            const fullPath = path.join(baseDir, item.name);
            const stats = await fs.stat(fullPath);
            
            if (item.isDirectory()) {
                // If it's a directory, get its contents
                const files = await fs.readdir(fullPath);
                const filesDetails = await Promise.all(files.map(async (fileName) => {
                    const filePath = path.join(fullPath, fileName);
                    const fileStats = await fs.stat(filePath);
                    return {
                        name: fileName,
                        path: `/public/${item.name}/${fileName}`, // URL path
                        size: fileStats.size,
                        created: fileStats.birthtime,
                        modified: fileStats.mtime
                    };
                }));
                
                return {
                    name: item.name,
                    type: 'directory',
                    path: `/public/${item.name}`,
                    created: stats.birthtime,
                    modified: stats.mtime,
                    files: filesDetails.sort((a, b) => b.modified - a.modified) // Sort files by date desc
                };
            } 
            return 
        }));
        
        // Sort the contents by modified date (newest first)
        const sortedContents = contents.sort((a, b) => b.modified - a.modified);
        
        response(req, res, {
            status: 200,
            message: "Folder contents retrieved successfully",
            data: sortedContents
        });
        
    } catch (error) {
        console.error('Error reading directory:', error);
        response(req, res, {
            status: 500,
            message: "Failed to retrieve folder contents",
            error: error.message
        });
    }
};