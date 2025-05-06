const Sequelize = require('sequelize');
module.exports = function(sequelize, DataTypes) {
  // Define the model
  const documents = sequelize.define('documents', {
    id: {
      autoIncrement: true,
      type: DataTypes.INTEGER,
      allowNull: false,
      primaryKey: true
    },
    category_id: {
      type: DataTypes.INTEGER,
      allowNull: false, // Assuming category_id is required
      references: {
        model: 'category',
        key: 'id'
      }
    },
    document_number: {
      type: DataTypes.STRING(255),
      allowNull: true
    },
    issued_date: {
      type: DataTypes.DATEONLY,
      allowNull: true
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
    tableName: 'documents',
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
        name: "category_id", // Corrected index name if it refers to category_id
        using: "BTREE",
        fields: [
          { name: "category_id" },
        ]
      },
    ]
  });

  // Add the associate method
  documents.associate = function(models) {
    // Document belongs to a Category
    documents.belongsTo(models.category, {
      foreignKey: 'category_id', // The foreign key in this table
      as: 'category' // Alias for the association
    });
    // Document has many ProductBatches
    documents.hasMany(models.product_batch, {
      foreignKey: 'document_id', // The foreign key in the product_batch table
      as: 'product_batches' // Alias for the association
    });
  };

  return documents; // Return the defined model
};
