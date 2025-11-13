# Known Issues

## Active Issues

No open issues.

## Fixed Issues

### Issue #1: Excel File Corruption
**Status**: Fixed 
**Priority**: High  
**Description**: Excel is detecting corruption in the workbook after our modifications and prompting to repair the file.  
**Severity**: Nuisance for the user that requires manual intervention and erodes customer trust.  
**Resolution**: Resolved with the replacement of the Transaction Type formula by direct text assignment (Re: Issue #2)

### Issue #2: Transaction Type Formula Not Applied Consistently
**Status**: Fixed  
**Priority**: High  
**Description**: The Transaction Type column (H) in the Details sheet does not consistently have the correct formula applied to all rows (both new and existing). Some cells remain empty or have incorrect formulas.
**Resolution**: Transaction Type formula replaced by logic with direct text assignment, which is more reliable.

### Issue #3: Data Validation Not Copied Correctly for Column L
**Status**: Fixed  
**Priority**: Medium  
**Description**: Data validation for column L (Subcategory) is not being copied correctly for some newly inserted rows. The validation appears to be copied from cells to the left instead of from cells above.  
**Expected Behavior**: New rows should inherit the same data validation dropdown options as existing rows in the same column.  
**Resolution**: fixed along with other Excel writing changes

### Issue #4: Date Deduplication Inconsistency
**Status**: Fixed  
**Priority**: Medium  
**Description**: Deduplication mismatch between Details sheet and account sheets causing inconsistent duplicate detection.
**Resolution**: Modified account sheet deduplication logic to always check existing Excel data first, then merge with cumulative keys, matching the Details sheet approach. Both sheets now use consistent deduplication behavior.
