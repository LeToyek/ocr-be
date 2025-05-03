const jwt = require("jsonwebtoken");
const response = require("../tools/response");
const { db } = require("../../config/sequelize");
const controller = require('../controllers/authController');
const { userSessionCache } = require('../tools/sessionCache');
const secretKey = process.env.JWT_SECRET;

// ROLES
// 1 = Superadmin
// 2 = Admin
// 3 = Approver
// 4 = User
// 5 = Checker

const verifyToken = (allowedRoles = [1, 2, 3, 4, 5, 6, 7]) => {
    return (req, res, next) => {
        const token = req.headers.authorization || req.cookies['SESSION-DIGIMOND'];

        if (!token) {
            return response(req, res, {
                status: 401,
                message: "Unauthorized - Token not provided",
            });
        }

        jwt.verify(token, secretKey, async (err, decoded) => {
            if (err) {
                // Remove cached data if token verification fails
                if (decoded && decoded.id) {
                    userSessionCache.delete(decoded.id);
                }

                return response(req, res, {
                    status: 401,
                    message: "Unauthorized - Invalid token",
                });
            }
            // Check if user data exists in the cache
            let userData = userSessionCache.get(decoded.id);

            // If not cached, query the database and cache it
            if (!userData) {
                console.log('Fetching user from database...');
                userData = await controller.loggedInUser({ user: decoded })                

                if (!userData) {
                    return response(req, res, {
                        status: 404,
                        message: "User Not Found",
                    });
                }

                // Cache the user data
                userSessionCache.set(decoded.id, userData);
            } else {
                console.log('Using cached user data...');
            }
            
            // Attach user data to the request object
            req.user = userData;            
            const userRoles = req.user ? req.user.role : [];
            
            // If userRoles is not an array, convert it into an array
            // const userRolesArray = Array.isArray(userRoles) ? userRoles : [userRoles];
            const userRolesArray = [1];
            
            // Check if the user has any of the allowed roles
            const hasAllowedRole = userRolesArray.some((role) => allowedRoles.includes(role));
            
            if (hasAllowedRole) {
                // If user is not (assuming role 1 is superadmin and 6 is fstl and 7 is director) and request has documentId param or query param id
                if (!userRolesArray.includes(1) && !userRolesArray.includes(6) && !userRolesArray.includes(7) && (req.params.documentId || req.query.id)) {
                    authorizeDocumentAccess(req, res, next);
                } else {
                    next();
                }
            } else {
                return response(req, res, {
                    status: 403,
                    code: req.method == 'GET' ? '-01' : '-03',
                    message: "Forbidden - Forbidden access",
                });
            }
        });
    };
};

const authorizeDocumentAccess = async (req, res, next) => {
    const documentId = req.params.documentId || req.query.id;
    const document = await db.digimond.document.findOne({
        where: {
            id: documentId,
        },
        include: [
            {
                model: db.digimond.mstUserAdditionalMap,
                as: "user_document_additional_mapping",
                where: {
                    user_id: req.user.id,
                },
                required: false,
            },
        ],
    });

    if (!document) {
        return response(req, res, {
            status: 404,
            message: "Resource not found",
        });
    }

    const userDocSections = req.user.document_sections;
    const userDocSubsections = req.user.document_subsections;
    const userAdditionalDocuments = req.user.additional_documents;

    let isSectionExist = false;
    let isSubsectionExist = false;
    let isAdditionalExist = false;

    if (document.document_subsection_id) {
        const checkSubsection = userDocSubsections.filter(
            (subsection) => subsection === document.document_subsection_id
        );

        isSubsectionExist = checkSubsection.length > 0 ? true : false;
    }

    if (document.document_section_id) {
        const checkSection = userDocSections.filter(
            (section) => section === document.document_section_id
        );

        isSectionExist = checkSection.length > 0 ? true : false;
    }

    if (document.user_document_additional_mapping.length > 0) {
        const checkAdditional = userAdditionalDocuments.filter(
            (additional) => additional === document.id
        );

        isAdditionalExist = checkAdditional.length > 0 ? true : false;
    }

    //  If either section or subsection or additional exist
    if (isSectionExist || isSubsectionExist || isAdditionalExist) {
        next();
    } else {
        return response(req, res, {
            status: 403,
            message: "Forbidden - Access denied",
            code: "-02",
        });
    }
};

module.exports = {
    verifyToken,
};
