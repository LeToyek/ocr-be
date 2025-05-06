"use strict";

const { db } = require("../../config/sequelize");
const { documents, product_batch, ocr_results } = db.lotnoOcr; // Destructure models
const response = require("../tools/response");
const { Op } = require("sequelize");
const moment = require("moment"); // Using moment for easier date calculations

/**
 * Calculates the start and end dates of the current week (Monday to Sunday).
 * @returns {{startOfWeek: Date, endOfWeek: Date}}
 */
const getCurrentWeekDates = () => {
    const today = moment();
    const startOfWeek = today.clone().startOf('isoWeek').toDate(); // Start of week (Monday)
    const endOfWeek = today.clone().endOf('isoWeek').toDate();     // End of week (Sunday)
    return { startOfWeek, endOfWeek };
};

/**
 * Verifies an OCR result against potential matching product batches based on
 * document date, verification status, and text matching.
 */
exports.verifyOcrResult = async (req, res) => {
    const { ocr_result_id,category_name } = req.body;

    if (!ocr_result_id) {
        return response(req, res, { status: 400, message: "Missing 'ocr_result_id' in request body." });
    }

    try {
        console.log(`Verification attempt initiated for OCR Result ID: ${ocr_result_id}`);

        // 1. Find the specific OCR Result by its ID to get the text to match against
        const targetOcrResult = await ocr_results.findByPk(ocr_result_id);

        // 2. Check if the target OCR Result was found
        if (!targetOcrResult) {
            console.log(`Target OCR Result ID ${ocr_result_id} not found.`);
            return response(req, res, { status: 404, message: `OCR Result with ID ${ocr_result_id} not found.` });
        }

        console.log(`Found target OCR Result: ${targetOcrResult.id}. Text to match: Top='${targetOcrResult.top_text}', Bottom='${targetOcrResult.bottom_text}'`);

        // 3. Find candidate Product Batches:
        //    - Not yet verified (is_verified = 0 or false)
        //    - Linked to a Document issued within the current week
        const { startOfWeek, endOfWeek } = getCurrentWeekDates();
        console.log(`Searching for unverified Product Batches linked to Documents issued between ${moment(startOfWeek).format('YYYY-MM-DD')} and ${moment(endOfWeek).format('YYYY-MM-DD')}`);

        const candidateProductBatches = await product_batch.findAll({
            where: {
                is_verified: {
                    [Op.or]: [false, 0, null] // Handle boolean, integer, or null for unverified
                }
            },
            include: [
                {
                    model: documents,
                    as: 'document', // Alias defined in product_batch model association
                    required: true, // INNER JOIN: Only include batches linked to a document
                    where: {
                        issued_date: {
                            [Op.between]: [startOfWeek, endOfWeek] // Document issued this week
                        }
                    },
                    include: [
                        {
                            model: db.lotnoOcr.category, // Explicitly reference category model from db
                            as: 'category', // Alias defined in documents model association
                            required: true, // INNER JOIN: Only include documents linked to a category
                            where: {
                                category_name: category_name.toLowerCase() // Filter by category_name from req.body
                            }
                        }
                    ]
                }
            ]
        });

        // 4. Check if any candidate Product Batches were found
        if (!candidateProductBatches || candidateProductBatches.length === 0) {
            console.log(`No unverified Product Batches found for documents issued this week.`);
            return response(req, res, { status: 404, code:'no_candidate', message: "Tidak ada lot number yang belum diverifikasi" });
        }

        console.log(`Found ${candidateProductBatches.length} candidate Product Batches.`);

        // 5. Iterate through candidates and match text
        let matchedProductBatch = null;
        for (const candidateBatch of candidateProductBatches) {
            console.log(`Comparing with Candidate Product Batch ID: ${candidateBatch.id} (Document: ${candidateBatch.document.id})`);
            console.log(`  Target OCR Top: '${targetOcrResult.top_text}' vs Candidate Batch Top: '${candidateBatch.top_text}'`);
            console.log(`  Target OCR Bottom: '${targetOcrResult.bottom_text}' vs Candidate Batch Bottom: '${candidateBatch.bottom_text}'`);

            const topMatch = targetOcrResult.top_text === candidateBatch.top_text;
            const bottomMatch = targetOcrResult.bottom_text === candidateBatch.bottom_text;

            if (topMatch && bottomMatch) {
                console.log(`Match found! Product Batch ID: ${candidateBatch.id}`);
                matchedProductBatch = candidateBatch;
                break; // Stop searching once a match is found
            } else {
                 console.log(`No match for Candidate Product Batch ID: ${candidateBatch.id}. Top Match: ${topMatch}, Bottom Match: ${bottomMatch}`);
            }
        }

        // 6. If a match was found, update the Product Batch status
        if (matchedProductBatch) {
            console.log(`Updating matched Product Batch ID ${matchedProductBatch.id} to verified.`);
            await matchedProductBatch.update({
                is_verified: true,
                updated_at: new Date(), // Manually set updated_at if timestamps: false
                ocr_result_id: targetOcrResult.id, // Link the OCR Result to the Product Batch
            });

            await targetOcrResult.update({
                product_batch_id: matchedProductBatch.id,
                updated_at: new Date(), // Manually set updated_at if timestamps: false
            });

            console.log(`Product Batch ID ${matchedProductBatch.id} successfully verified.`);
            response(req, res, {
                status: 200,
                code: 'success',
                message: `Product Batch ${matchedProductBatch.id} successfully verified against OCR Result ${targetOcrResult.id}.`,
                data: {
                    product_batch_id: matchedProductBatch.id,
                    ocr_result_id: targetOcrResult.id,
                    document_id: matchedProductBatch.document.id, // Access document via the matched batch
                }
            });
        } else {
            // 7. If no match was found after checking all candidates
            console.log(`No matching Product Batch found for OCR Result ID ${targetOcrResult.id} among the candidates.`);
            response(req, res, {
                status: 404, // Or 400 depending on desired semantics
                message: `Tidak ada Product Batch yang cocok untuk OCR Result ID ${targetOcrResult.id}`,
                code:'no_match',
                data: {
                    ocr_result_id: targetOcrResult.id,
                    ocr_top: targetOcrResult.top_text,
                    ocr_bottom: targetOcrResult.bottom_text,
                    candidates_checked: candidateProductBatches.length
                }
            });
        }

    } catch (error) {
        console.error("Error during verification process:", error);
        response(req, res, {
            status: 500,
            code:'error',
            message: "An error occurred during the verification process.",
            error: error.message
        });
    }
};
