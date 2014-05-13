# Checks whether a given binary number input is divisible by 3 (0b11),
# keeping "0" (for False) or "1" (for True) on the resulting tape

# Every digit d appended to x makes the new number y = x * 2 + d,
# and the same follows in modulo 3
mod0
  0    -> R mod0
  1    -> R mod1
  None -> L return_T
mod1
  0    -> R mod2
  1    -> R mod0
  None -> L return_F
mod2
  0    -> R mod1
  1    -> R mod2
  None -> L return_F

# Clears the tape and "prints" to it the desired result
return_T
  [0 1] -> E L return_T
  None  -> R P1 loop
return_F
  [0 1] -> E L return_F
  None  -> R P0 loop

# Ending deadlock
loop -> loop

