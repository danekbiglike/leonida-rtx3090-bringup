fn main() {
    use std::{hint::black_box, time::Instant};
    let mut seed=1234u64;
    let mut rand=|limit:u64| {seed=seed.wrapping_mul(6364136223846793005).wrapping_add(1);(seed>>32)%limit};
    for _ in 0..10000 {
        let operations=(0..rand(64)).map(|_| {
            let src=rand(2048) as usize; let asked=rand(2)==0;
            match rand(15) {
                0=>Does::Run,
                1=>Does::Read {from:src,to:src+64,asked},
                2=>Does::Refresh {shadow:1,from:src,to:src+128},
                3=>Does::Copy {dst:src+128,src,len:32,asked},
                4=>Does::Placed {dst:src+96,src,len:64},
                _=>Does::Fill {src,len:64,asked,to:rand(6)!=0},
            }
        }).collect::<Vec<_>>();
        for stage in [1,2] {for order in [false,true] {
            let mut a=None;let mut b=None;
            assert_eq!(baseline(&operations,stage,order,&mut a),fast(&operations,stage,order,&mut b));
            assert_eq!(a,b);
        }}
    }
    for n in [160usize, 6000, 12289] {
        let series=(0..n).map(|i|Does::Fill{src:(i*19%113)*256+0x10000,len:480,asked:true,to:true}).collect::<Vec<_>>();
        assert_eq!(baseline(&series,2,true,&mut None),fast(&series,2,true,&mut None));
    }
    println!("round,planner,microseconds_per_6000_fills");
    for round in 0..12 {
        let lists=(0..30).map(|k| (0..200).map(|i| Does::Fill{src:0x10000+((i*19+k)%113)*256,len:480,asked:true,to:true}).collect::<Vec<_>>()).collect::<Vec<_>>();
        for v in [round%2,1-round%2] {
            let now=Instant::now();
            for _ in 0..40 {for ops in &lists {
                let got=if v==0{baseline(black_box(ops),2,true,&mut None)}else{fast(black_box(ops),2,true,&mut None)};
                black_box(got.unwrap());
            }}
            println!("{round},{},{:.3}",if v==0{"baseline"}else{"candidate"},now.elapsed().as_secs_f64()*1e6/40.0);
        }
    }
}
