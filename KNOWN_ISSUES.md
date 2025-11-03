# Known Issues

## Active Issues

### Issue #1: Excel File Corruption
**Status**: Open  
**Priority**: High  
**Description**: Excel is detecting corruption in the workbook after our modifications and prompting to repair the file.

**Expected Behavior**: Workbook should remain valid and open without corruption warnings.

**Current Behavior**: Excel shows "We found a problem with some content in 'FinanceWorkbook 2025.xlsx'" and offers to repair the file.

**Impact**:
- User workflow disruption
- Potential data loss during repair process
- Loss of trust in the tool's reliability

**Severity**: Nuisance for the user that requires manual intervention and erodes customer trust.

### Issue #2: Transaction Type Formula Not Applied Consistently
**Status**: Open  
**Priority**: High  
**Description**: The Transaction Type column (H) in the Details sheet does not consistently have the correct formula applied to all rows (both new and existing). Some cells remain empty or have incorrect formulas.

**Expected Behavior**: All rows should have the formula:
```
=IFERROR(IFS(AND(ISNUMBER(VALUE(F2)),ISNUMBER(VALUE(G2)),F2<>0,G2<>0),"Error",F2<0,"Withdrawal",G2>0,"Deposit"),"")
```

**Current Behavior**: 
- Some rows have no formula (empty cells)
- Some rows have formulas with `@` symbols added by Excel
- Inconsistent application across new and existing rows

### Issue #3: Data Validation Not Copied Correctly for Column L
**Status**: Open  
**Priority**: Medium  
**Description**: Data validation for column L (Type) is not being copied correctly for some newly inserted rows. The validation appears to be copied from cells to the left instead of from cells above.

**Expected Behavior**: New rows should inherit the same data validation dropdown options as existing rows in the same column.

**Current Behavior**: Some rows show incorrect validation options or validation that appears to come from adjacent columns rather than the column above.

**Impact**: Users may see incorrect dropdown options when editing the Type field for new transactions, and also a data validation warning on cells generated or updated by this tool.  

## Fixed Issues

None yet.
