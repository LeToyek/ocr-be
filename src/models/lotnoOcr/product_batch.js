const Sequelize = require('sequelize');
module.exports = function(sequelize, DataTypes) {
  // Define the model
  const product_batch = sequelize.define('product_batch', {
    id: {
      autoIncrement: true,
      type: DataTypes.INTEGER,
      allowNull: false,
      primaryKey: true
    },
    document_id: {
      type: DataTypes.INTEGER,
      allowNull: true, // Or false if required
      references: {
        model: 'documents',
        key: 'id'
      }
    },
    // ocr_result_id is removed from associations logic, assuming ocr_results links back
    ocr_result_id: {
      type: DataTypes.INTEGER,
      allowNull: true,
      references: {
        model: 'ocr_results',
        key: 'id'
      }
    },
    top_text: {
      type: DataTypes.TEXT,
      allowNull: true
    },
    bottom_text: {
      type: DataTypes.TEXT,
      allowNull: true
    },
    is_verified: {
      type: DataTypes.BOOLEAN,
      allowNull: true,
      defaultValue: 0
    },
    created_at: {
      type: DataTypes.DATE,
      allowNull: true
    },
    updated_at: {
      type: DataTypes.DATE,
      allowNull: true
    }
  }, {
    sequelize,
    tableName: 'product_batch',
    timestamps: false,
    underscored: true,
    indexes: [
      {
        name: "PRIMARY",
        unique: true,
        using: "BTREE",
        fields: [
          { name: "id" },
        ]
      },
      {
        name: "document_id",
        using: "BTREE",
        fields: [
          { name: "document_id" },
        ]
      },
      // Index for ocr_result_id might still be useful for direct lookups if needed
      // {
      //   name: "product_batch_ibfk_2", // Or a more descriptive name
      //   using: "BTREE",
      //   fields: [
      //     { name: "ocr_result_id" },
      //   ]
      // },
    ]
  });

  // Add the associate method
  product_batch.associate = function(models) {
    // ProductBatch belongs to a Document
    product_batch.belongsTo(models.documents, {
      foreignKey: 'document_id', // The foreign key in this table
      as: 'document' // Alias for the association
    });
    // ProductBatch has many OcrResults
    product_batch.hasMany(models.ocr_results, {
      foreignKey: 'product_batch_id', // The foreign key in the ocr_results table
      as: 'ocr_results' // Alias for the association
    });
  };

  return product_batch; // Return the defined model
};
