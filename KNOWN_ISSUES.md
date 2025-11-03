# Known Issues

## Active Issues

### Transaction Type Formula Not Applied Consistently
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
