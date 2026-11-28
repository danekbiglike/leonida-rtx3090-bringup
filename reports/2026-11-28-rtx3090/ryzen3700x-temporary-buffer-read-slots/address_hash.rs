#[derive(Default)]
pub(crate) struct AddressHash(u64);

impl std::hash::Hasher for AddressHash {
    fn finish(&self) -> u64 {
        self.0
    }
    fn write(&mut self, bytes: &[u8]) {
        for &b in bytes {
            self.write_usize(usize::from(b));
        }
    }
    fn write_usize(&mut self, n: usize) {
        let h = (self.0.rotate_left(5) ^ n as u64).wrapping_mul(0x9E37_79B9_7F4A_7C15);
        self.0 = h ^ (h >> 32);
    }
    fn write_u64(&mut self, n: u64) {
        self.write_usize(n as usize);
    }
    fn write_u32(&mut self, n: u32) {
        self.write_usize(n as usize);
    }
}
