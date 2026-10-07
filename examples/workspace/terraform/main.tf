# SYNTHETIC example. Not applied anywhere.
resource "azurerm_storage_account" "lake" {
  name                     = "stlakehouse"
  resource_group_name      = "rg-data"
  location                 = "brazilsouth"
  account_tier             = "Standard"
  account_replication_type = "ZRS"
  is_hns_enabled           = true
}

resource "azurerm_databricks_workspace" "analytics" {
  name                = "dbw-analytics"
  resource_group_name = "rg-data"
  location            = "brazilsouth"
  sku                 = "premium"
}

# Same display name exists in two subscriptions; no binding declared on purpose.
resource "azurerm_storage_account" "stshared" {
  name                     = "stshared"
  resource_group_name      = "rg-data"
  location                 = "brazilsouth"
  account_tier             = "Standard"
  account_replication_type = "LRS"
}
