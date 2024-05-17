# pure
Experiments around writing and detecting pure functions


## Usage

### macOS

If you've installed llvm using homebrew, you may need to run the following in
order for libclang to be able to find the library binaries.
```bash
export DYLD_LIBRARY_PATH="/opt/homebrew/opt/llvm/lib:$DYLD_LIBRARY_PATH"
```
