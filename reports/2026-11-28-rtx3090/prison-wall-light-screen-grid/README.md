# Screen grid in the block-shaped prison wall light

The two photos show the same two spots of sunlight on the cell wall. In one frame bright rings with rectangular steps surround the spots. In the other frame the spots have soft edges. The crop below is unchanged RGB at the original screenshot scale. [Paired crops](wall-crops.png)

The stepped boundary lines up with a **160 × 90 screen grid**. The photographed client area is 1,818 × 993 pixels. This gives grid spacing of 11.36 pixels across and 11.03 pixels down. At a red threshold of 190, **277 of 369** vertical edge pixels and **378 of 518** horizontal edge pixels fall within 1.25 pixels of this grid. Moving the grid half a cell leaves **24** and **44**. The soft-edged image has just 33 and 64 eligible pixels; 0 and 16 fall on the grid. [All four thresholds and phase offsets](wall-boundaries.csv)

The region spans x 754–1026 and y 200–352 in each source. The mask uses red at or above the stated threshold, red minus green above 20, and green minus blue above 22. Only straight horizontal or vertical boundary runs of at least six pixels contribute. Counts describe edge length; neighboring pixels in a run are not independent observations. The camera moved slightly between the two images.

VIctory's indirect lighting estimate has 160 × 90 points. A game pass with the same screen tiling could give the same alignment. The two snapshots identify a spatial scale but cannot assign the artifact to a pass. A build with an independent 192 × 108 indirect-light grid can test whether the boundary moves when the grid changes. Neither photo measures the performance or appearance of that change.

To reproduce the CSV from the lossless public crops with Pillow, run `python measure_wall.py wall-crops.png wall-crops.png . --from-sheet`. [Measurement script](measure_wall.py)
