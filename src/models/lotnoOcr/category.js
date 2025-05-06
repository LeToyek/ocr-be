const Sequelize = require('sequelize');
module.exports = function(sequelize, DataTypes) {
  // Define the model
  const category = sequelize.define('category', {
    id: {
      autoIncrement: true,
      type: DataTypes.INTEGER,
      allowNull: false,
      primaryKey: true
    },
    category_name: {
      type: DataTypes.STRING(255),
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
    tableName: 'category',
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
    ]
  });

  // Add the associate method
  category.associate = function(models) {
    // Category has many Documents
    category.hasMany(models.documents, {
      foreignKey: 'category_id', // The foreign key in the documents table
      as: 'documents' // Alias for the association
    });
  };

  return category; // Return the defined model
};
