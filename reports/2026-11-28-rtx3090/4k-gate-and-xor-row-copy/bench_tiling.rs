use std::hint::black_box;
use std::time::Instant;
use bench_texture::{Desc, Dimension, Layout, Swizzle};

fn main() {
    for (w, h, n) in [(256u32, 256u32, 4usize), (256, 256, 8), (513, 357, 4), (1920, 1080, 4)] {
        let desc = Desc {
            dimension: Dimension::Tex2d, width: w, height: h, depth: 1, mips: 1,
            element_bytes: n as u32, block: 1, samples: 1, swizzle: Swizzle::SW_64KB_R_X,
        };
        let layout = Layout::new(&desc).unwrap();
        let pitch = (w as usize * n).next_multiple_of(256);
        let input: Vec<u8> = (0..pitch * h as usize).map(|i| (i.wrapping_mul(0x9e3779b9) >> 12) as u8).collect();
        let mut tiled = vec![0u8; layout.size as usize];
        let mut linear = vec![0u8; input.len()];
        for iter in 0..29 {
            let start = Instant::now();
            layout.tile(black_box(&mut tiled), 0, 0, black_box(&input), pitch, 0).unwrap();
            let tile_ns = start.elapsed().as_nanos();
            let start = Instant::now();
            layout.detile(black_box(&tiled), 0, 0, black_box(&mut linear), pitch, 0).unwrap();
            let detile_ns = start.elapsed().as_nanos();
            if iter == 0 {
                for (src, dst) in input.chunks_exact(pitch).zip(linear.chunks_exact(pitch)) {
                    assert_eq!(&src[..w as usize * n], &dst[..w as usize * n]);
                }
            }
            if iter >= 5 {
                println!("{w},{h},{n},{iter},{tile_ns},{detile_ns}");
            }
        }
    }
}
