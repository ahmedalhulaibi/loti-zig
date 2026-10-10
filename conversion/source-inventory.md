# Original C and io_uring inventory

Snapshot: `c9ee2424af02e4c1e4765088580107d5e17b826e`. Regenerate: `python3 tools/inventory.py`.

`source-inventory.json` enumerates every matched original line, its exact
text, and categories. Complete C blocks include lines without API names.

Matched lines: **3447**. C blocks/declarations: **104**. API symbols: **76**.

## Per-file line coverage

| File | Original lines |
|---|---|
| `async_intro.rst` | 58, 79, 81 |
| `changelog.rst` | 9, 10 |
| `conf.py` | 20, 48 |
| `delme.c` | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94, 95, 96, 97, 98, 99, 100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119, 120, 121, 122, 123, 124, 125, 126, 127, 128, 129, 130, 131, 132, 133, 134, 135, 136, 137, 138, 139, 140, 141, 142, 143, 144, 145, 146, 147, 148, 149, 150, 151, 152, 153, 154, 155, 156, 157, 158, 159, 160, 161, 162, 163, 164, 165, 166, 167, 168, 169, 170, 171, 172, 173, 174, 175, 176, 177, 178, 179, 180, 181, 182, 183, 184, 185, 186, 187, 188, 189, 190, 191, 192, 193, 194, 195, 196, 197, 198, 199, 200, 201, 202, 203, 204, 205, 206, 207, 208, 209, 210, 211, 212, 213, 214, 215, 216, 217, 218, 219, 220, 221, 222, 223, 224, 225, 226 |
| `index.rst` | 6, 9, 14, 32, 52, 53, 55, 56, 57, 58, 59, 60, 61, 62, 66, 70, 71, 72 |
| `low_level.rst` | 3, 5, 13, 15, 17, 21, 23, 24, 25, 26, 27, 28, 29, 33, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 71, 76, 78, 80, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94, 95, 96, 97, 98, 99, 100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119, 120, 121, 122, 123, 124, 125, 126, 127, 128, 129, 130, 131, 132, 133, 134, 135, 136, 137, 138, 139, 140, 141, 142, 143, 144, 145, 146, 147, 148, 149, 150, 151, 152, 153, 154, 155, 156, 157, 158, 159, 160, 161, 162, 163, 164, 165, 166, 167, 168, 169, 170, 171, 172, 173, 174, 175, 176, 177, 178, 179, 180, 181, 182, 183, 184, 185, 186, 187, 188, 189, 190, 191, 192, 193, 194, 195, 196, 197, 198, 199, 200, 201, 202, 203, 204, 205, 206, 207, 208, 209, 210, 211, 212, 213, 214, 215, 216, 217, 218, 219, 220, 221, 222, 223, 224, 225, 226, 227, 228, 229, 230, 231, 232, 233, 234, 235, 236, 237, 238, 239, 240, 241, 242, 243, 244, 245, 246, 247, 248, 249, 250, 251, 252, 253, 254, 255, 256, 257, 258, 259, 260, 261, 262, 263, 264, 265, 266, 267, 268, 269, 270, 271, 272, 273, 274, 275, 276, 277, 278, 279, 280, 281, 282, 283, 284, 285, 286, 287, 288, 289, 290, 291, 292, 293, 294, 295, 296, 297, 298, 299, 300, 301, 302, 303, 304, 305, 306, 307, 308, 309, 310, 311, 312, 313, 314, 315, 316, 317, 318, 319, 320, 321, 322, 323, 324, 325, 326, 327, 328, 329, 330, 331, 332, 333, 334, 335, 336, 337, 338, 339, 340, 341, 342, 343, 344, 345, 346, 347, 348, 349, 350, 351, 352, 353, 354, 355, 356, 357, 358, 359, 360, 361, 362, 363, 364, 365, 366, 367, 368, 369, 370, 371, 372, 373, 374, 375, 376, 377, 378, 379, 380, 381, 382, 383, 384, 385, 386, 387, 388, 389, 390, 391, 392, 393, 394, 395, 396, 397, 398, 399, 400, 401, 402, 403, 404, 405, 406, 407, 408, 409, 410, 411, 412, 413, 414, 415, 416, 417, 418, 419, 420, 421, 422, 423, 424, 425, 426, 427, 428, 429, 430, 431, 432, 433, 434, 435, 436, 437, 438, 439, 440, 441, 442, 443, 444, 445, 446, 447, 448, 449, 450, 451, 452, 453, 454, 462, 464, 465, 466, 467, 468, 469, 470, 471, 472, 473, 474, 475, 477, 479, 481, 482, 483, 484, 485, 486, 487, 488, 489, 490, 491, 492, 493, 494, 495, 496, 497, 498, 499, 500, 501, 502, 503, 504, 505, 506, 507, 508, 511, 515, 519, 523, 525, 531, 532, 533, 534, 535, 536, 537, 538, 539, 540, 541, 542, 543, 544, 545, 546, 547, 548, 550, 556, 557, 558, 559, 560, 561, 562, 563, 564, 565, 566, 567, 568, 569, 570, 572 |
| `ref-iouring/index.rst` | 1, 9, 10, 11 |
| `ref-iouring/io_uring_enter.rst` | 1, 3, 6, 13, 15, 20, 22, 24, 26, 28, 30, 31, 32, 40, 41, 53, 56, 60, 67, 81, 116, 118, 120, 122, 126, 128, 130, 133, 143, 150, 152, 155, 163, 171, 178, 179, 180, 182, 190, 191, 192, 194, 198, 204, 211, 221, 228, 239, 241, 242, 244, 250, 253, 260, 267, 275, 282, 289, 297, 302, 310, 312, 316, 317, 321, 332, 334, 335, 346, 347, 365, 379, 392, 393, 395, 402, 413, 414, 420, 430, 443, 449, 476, 482, 484, 495, 496, 497, 500, 501, 505, 509, 510, 511, 516, 517, 519, 523, 527, 530, 538 |
| `ref-iouring/io_uring_register.rst` | 1, 3, 6, 13, 15, 20, 21, 27, 29, 43, 44, 45, 55, 62, 64, 66, 69, 74, 78, 84, 87, 91, 96, 101, 103, 106, 108, 113, 114, 118, 120, 126, 127, 128, 129, 131, 133, 136, 138, 145, 147, 153, 163, 171, 175, 179, 183, 187, 200, 204 |
| `ref-iouring/io_uring_setup.rst` | 1, 3, 6, 13, 15, 20, 23, 32, 45, 48, 57, 58, 60, 62, 70, 72, 75, 84, 85, 91, 92, 95, 97, 98, 101, 102, 106, 107, 115, 120, 121, 130, 134, 136, 137, 145, 146, 148, 150, 153, 154, 157, 185, 188, 200, 201, 219, 221, 243, 245, 247, 248, 253, 256, 268, 269, 270, 271, 286, 292 |
| `ref-liburing/advanced_usage.rst` | 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 24, 31, 32, 33, 34, 35, 36, 37, 38, 39, 44, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 66, 73, 74, 75, 76, 77, 78, 79, 80, 81, 86, 93, 94, 95, 96, 97, 98, 99, 100, 101, 102, 103, 104, 108, 115, 116, 117, 118, 119, 120, 121, 122, 123, 124, 128, 135, 136, 137, 138, 139, 140, 141, 142, 143, 144, 148, 155, 156, 157, 158, 159, 160, 161, 162, 163, 167, 174, 175, 176, 177, 178, 179, 180, 181, 182, 189, 190, 191, 192, 193, 194, 195, 196, 197, 198 |
| `ref-liburing/completion.rst` | 9, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 36, 37, 38, 39, 40, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 97, 98, 99, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 118, 119, 120, 121, 122, 123, 124, 125, 126, 127, 128, 129, 130, 134, 135, 136, 137, 138, 139, 140, 141, 142, 143, 144, 148, 149, 150, 151, 152, 153, 154, 155, 159, 160, 161 |
| `ref-liburing/cqe.rst` | 8, 10, 12, 13, 14, 15, 16, 17, 18 |
| `ref-liburing/index.rst` | 1, 7 |
| `ref-liburing/setup_teardown.rst` | 7, 9, 10, 11, 12, 13, 14, 15, 16, 17, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 80, 81, 82, 83, 84, 85, 86, 90, 91, 92, 93, 94, 95, 96, 97, 98, 99, 100, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 118, 119, 120, 121, 122, 123, 124 |
| `ref-liburing/sqe.rst` | 5, 8, 11, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60 |
| `ref-liburing/submission.rst` | 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 24, 26, 28, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 51, 52, 53, 54, 55, 56, 57, 58, 62, 63, 64, 65, 66, 67, 68, 69, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 89, 90, 91, 92, 93, 94, 95, 96, 97, 107, 114, 115, 116, 117, 118, 119, 120, 127, 128, 129, 130, 131, 132, 133, 134, 135, 136, 137, 138, 139, 140, 141, 148, 149, 150, 151, 152, 153, 154, 155, 156, 157, 158, 159, 160, 161, 162, 169, 170, 171, 172, 173, 174, 175, 176, 177, 178, 179, 180, 181, 182, 183, 190, 191, 192, 193, 194, 195, 196, 197, 198, 199, 200, 201, 202, 203, 204, 205, 206, 213, 214, 215, 216, 217, 218, 219, 220, 221, 222, 223, 224, 225, 226, 227, 234, 235, 236, 237, 238, 239, 240, 241, 242, 243, 244, 245, 246, 247, 248, 249, 250, 251, 252, 259, 260, 261, 262, 263, 264, 265, 266, 267, 268, 269, 270, 271, 272, 273, 274, 275, 276, 283, 284, 285, 286, 287, 288, 289, 290, 291, 292, 293, 300, 301, 302, 303, 304, 305, 306, 307, 308, 309, 310, 311, 312, 313, 314, 321, 322, 323, 324, 325, 326, 327, 328, 329, 330, 331, 332, 333, 334, 341, 342, 343, 344, 345, 346, 347, 348, 349, 350, 351, 352, 353, 354, 361, 362, 363, 364, 365, 366, 367, 368, 369, 370, 371, 372, 373, 380, 381, 382, 383, 384, 385, 386, 387, 388, 389, 390, 391, 392, 399, 400, 401, 402, 403, 404, 405, 406, 407, 408, 409, 410, 418, 419, 420, 421, 422, 423, 424, 425, 426, 427, 428, 429, 430, 431, 432, 433, 434, 435, 442, 443, 444, 445, 446, 447, 448, 449, 450, 451, 452, 453, 454, 461, 462, 463, 464, 465, 466, 473, 474, 475, 476, 477, 478, 479, 480, 481, 482, 483, 484, 485, 486, 493, 494, 495, 496, 497, 498, 505, 506, 507, 508, 509, 510, 511, 512, 513, 514, 515, 516, 517, 518, 525, 526, 527, 528, 529, 530, 531, 532, 533, 534, 535, 536, 537, 544, 545, 546, 547, 548, 549, 550, 551, 552, 553, 554, 555, 556, 557, 558, 565, 566, 567, 568, 569, 570, 571, 572, 573, 574, 575, 576, 583, 584, 585, 586, 587, 588, 589, 590, 591, 592, 593 |
| `ref-liburing/supported_caps.rst` | 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 20, 21, 22, 23, 24, 25, 26, 27, 28, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 51, 52, 53, 54, 55, 56, 57, 58, 62, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94, 95 |
| `tutorial/cat_liburing.rst` | 3, 5, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94, 95, 96, 97, 98, 99, 100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119, 120, 121, 122, 123, 124, 125, 126, 127, 128, 129, 130, 131, 132, 133, 134, 135, 136, 137, 138, 139, 140, 141, 142, 143, 144, 145, 146, 147, 148, 149, 150, 151, 152, 153, 154, 155, 156, 157, 158, 159, 160, 161, 162, 163, 164, 165, 166, 167, 168, 169, 170, 171, 172, 173, 177, 178, 180, 182, 183, 184, 188, 189, 190, 191, 192, 193, 194, 195, 196, 197, 201, 202, 203, 204, 205, 211, 212, 213, 214, 215, 216, 217, 218 |
| `tutorial/cp_liburing.rst` | 3, 6, 8, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94, 95, 96, 97, 98, 99, 100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119, 120, 121, 122, 123, 124, 125, 126, 127, 128, 129, 130, 131, 132, 133, 134, 135, 136, 137, 138, 139, 140, 141, 142, 143, 144, 145, 146, 147, 148, 149, 150, 151, 152, 153, 154, 155, 156, 157, 158, 159, 160, 161, 162, 163, 164, 165, 166, 167, 168, 169, 170, 171, 172, 173, 174, 175, 176, 177, 178, 179, 180, 181, 182, 183, 184, 185, 186, 187, 188, 189, 190, 191, 192, 193, 194, 195, 196, 197, 198, 199, 200, 201, 202, 203, 204, 205, 206, 207, 208, 209, 210, 211, 212, 213, 214, 215, 216, 217, 218, 219, 220, 221, 222, 223, 224, 225, 226, 227, 228, 229, 230, 231, 232, 233, 234, 235, 236, 237, 238, 239, 240, 241, 242, 243, 244, 245, 246, 247, 248, 249, 250, 251, 252, 253, 254, 255, 260 |
| `tutorial/fixed_buffers.rst` | 6, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94, 95, 96, 97, 98, 99, 100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119, 120, 121, 122, 123, 124, 125, 126, 130, 132 |
| `tutorial/index.rst` | 1, 3 |
| `tutorial/link_liburing.rst` | 5, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 88, 90, 102, 106, 107, 108, 112, 113, 114, 126 |
| `tutorial/probe_liburing.rst` | 5, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94, 95, 96, 97, 98, 99, 100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110 |
| `tutorial/register_eventfd.rst` | 7, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94, 95, 96, 97, 98, 99, 100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 118, 120 |
| `tutorial/sq_poll.rst` | 6, 8, 12, 18, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94, 95, 96, 97, 98, 99, 100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119, 120, 121, 122, 123, 124, 125, 126, 127, 128, 129, 130, 131, 132, 133, 134, 135, 136, 137, 138, 139, 140, 141, 142, 143, 144, 145, 146, 147, 148, 149, 150, 151, 152, 153, 154, 155, 156, 157, 158, 159, 160, 161, 162, 163, 164, 165, 166, 170, 172, 174, 176, 178, 184, 187, 188, 197, 199, 203, 210, 214, 215, 216, 217, 218 |
| `tutorial/webserver_liburing.rst` | 3, 6, 8, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94, 95, 96, 97, 98, 99, 100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119, 120, 121, 122, 123, 124, 125, 126, 127, 128, 129, 130, 131, 132, 133, 134, 135, 136, 137, 138, 139, 140, 141, 142, 143, 144, 145, 146, 147, 148, 149, 150, 151, 152, 153, 154, 155, 156, 157, 158, 159, 160, 161, 162, 163, 164, 165, 166, 167, 168, 169, 170, 171, 172, 173, 174, 175, 176, 177, 178, 179, 180, 181, 182, 183, 184, 185, 186, 187, 188, 189, 190, 191, 192, 193, 194, 195, 196, 197, 198, 199, 200, 201, 202, 203, 204, 205, 206, 207, 208, 209, 210, 211, 212, 213, 214, 215, 216, 217, 218, 219, 220, 221, 222, 223, 224, 225, 226, 227, 228, 229, 230, 231, 232, 233, 234, 235, 236, 237, 238, 239, 240, 241, 242, 243, 244, 245, 246, 247, 248, 249, 250, 251, 252, 253, 254, 255, 256, 257, 258, 259, 260, 261, 262, 263, 264, 265, 266, 267, 268, 269, 270, 271, 272, 273, 274, 275, 276, 277, 278, 279, 280, 281, 282, 283, 284, 285, 286, 287, 288, 289, 290, 291, 292, 293, 294, 295, 296, 297, 298, 299, 300, 301, 302, 303, 304, 305, 306, 307, 308, 309, 310, 311, 312, 313, 314, 315, 316, 317, 318, 319, 320, 321, 322, 323, 324, 325, 326, 327, 328, 329, 330, 331, 332, 333, 334, 335, 336, 337, 338, 339, 340, 341, 342, 343, 344, 345, 346, 347, 348, 349, 350, 351, 352, 353, 354, 355, 356, 357, 358, 359, 360, 361, 362, 363, 364, 365, 366, 367, 368, 369, 370, 371, 372, 373, 374, 375, 376, 377, 378, 379, 380, 381, 382, 383, 384, 385, 386, 387, 388, 389, 390, 391, 392, 393, 394, 395, 396, 397, 398, 399, 400, 401, 402, 403, 404, 405, 406, 407, 408, 409, 410, 411, 412, 413, 414, 415, 416, 417, 418, 419, 420, 421, 422, 423, 424, 425, 426, 427, 428, 429, 430, 431, 432, 433, 434, 435, 436, 437, 438, 439, 440, 441, 442, 443, 444, 445, 446, 447, 448, 449, 450, 451, 452, 453, 454, 455, 456, 457, 458, 459, 460, 461, 462, 463, 464, 465, 486, 488, 490, 491, 492, 493, 494, 495, 496, 497, 498, 499, 500, 501, 502, 503, 504, 505, 506, 507, 508, 509, 510, 511, 512, 513, 514, 515, 516, 517, 518, 519, 520, 521, 522, 523, 524, 525, 526, 527, 528, 529, 530, 531, 532, 533, 537, 538, 539, 540, 541, 542, 543, 544, 545, 546, 547, 548, 549, 551, 553, 554, 555, 556, 557, 558, 559, 560, 568, 569, 570, 571, 572, 573, 574, 576, 578, 579, 580, 581, 582, 583, 584, 585, 586, 587, 588, 589, 590, 591, 592, 593, 595, 597, 598, 599, 600, 601, 602, 603, 604, 605, 606, 607, 611, 612, 613, 614, 615, 616, 617, 618, 619, 623, 624, 625, 626, 627, 628, 629, 630, 631, 632, 636, 637, 638, 639, 640, 641, 642, 643, 644 |
| `what_is_io_uring.rst` | 1, 3, 5, 8, 10, 18, 21, 22, 23, 24, 28, 33, 35, 37, 39, 41, 43, 47, 49, 51, 53 |

## C blocks and declarations

| Original location | Kind | Declaration |
|---|---|---|
| `low_level.rst:23-29` | `code-block` | `c` |
| `low_level.rst:45-67` | `code-block` | `c` |
| `low_level.rst:82-454` | `code-block` | `c` |
| `low_level.rst:464-475` | `code-block` | `c` |
| `low_level.rst:481-508` | `code-block` | `c` |
| `low_level.rst:531-548` | `code-block` | `c` |
| `low_level.rst:556-570` | `code-block` | `c` |
| `ref-iouring/io_uring_enter.rst:15-15` | `c:function` | `int io_uring_enter(unsigned int fd, unsigned int to_submit, unsigned int min_complete, unsigned int flags, sigset_t *sig)` |
| `ref-iouring/io_uring_register.rst:15-15` | `c:function` | `int io_uring_register(unsigned int fd, unsigned int opcode, void *arg, unsigned int nr_args)` |
| `ref-iouring/io_uring_setup.rst:15-15` | `c:function` | `int io_uring_setup(u32 entries, struct io_uring_params *p)` |
| `ref-liburing/advanced_usage.rst:9-19` | `c:function` | `int io_uring_register_buffers(struct io_uring *ring, const struct iovec *iovecs, unsigned nr_iovecs)` |
| `ref-liburing/advanced_usage.rst:31-39` | `c:function` | `int io_uring_unregister_buffers(struct io_uring *ring)` |
| `ref-liburing/advanced_usage.rst:51-61` | `c:function` | `int io_uring_register_files(struct io_uring *ring, const int *files, unsigned nr_files)` |
| `ref-liburing/advanced_usage.rst:73-81` | `c:function` | `int io_uring_unregister_files(struct io_uring *ring)` |
| `ref-liburing/advanced_usage.rst:93-104` | `c:function` | `int io_uring_register_files_update(struct io_uring *ring, unsigned off, int *files, unsigned nr_files)` |
| `ref-liburing/advanced_usage.rst:115-124` | `c:function` | `int io_uring_register_eventfd(struct io_uring *ring, int fd)` |
| `ref-liburing/advanced_usage.rst:135-144` | `c:function` | `int io_uring_register_eventfd_async(struct io_uring *ring, int fd)` |
| `ref-liburing/advanced_usage.rst:155-163` | `c:function` | `int io_uring_unregister_eventfd(struct io_uring *ring)` |
| `ref-liburing/advanced_usage.rst:174-182` | `c:function` | `int io_uring_register_personality(struct io_uring *ring)` |
| `ref-liburing/advanced_usage.rst:189-198` | `c:function` | `int io_uring_unregister_personality(struct io_uring *ring, int id)` |
| `ref-liburing/completion.rst:11-34` | `code-block` | `c` |
| `ref-liburing/completion.rst:45-56` | `c:function` | `int io_uring_wait_cqe(struct io_uring *ring, struct io_uring_cqe **cqe_ptr)` |
| `ref-liburing/completion.rst:60-72` | `c:function` | `int io_uring_wait_cqe_nr(struct io_uring *ring, struct io_uring_cqe **cqe_ptr, unsigned wait_nr)` |
| `ref-liburing/completion.rst:76-93` | `c:function` | `int io_uring_wait_cqes(struct io_uring *ring, struct io_uring_cqe **cqe_ptr, unsigned wait_nr, struct __kernel_timespec *ts, sigset_t *sigmask)` |
| `ref-liburing/completion.rst:97-99` | `c:function` | `int io_uring_wait_cqe_timeout(struct io_uring *ring, struct io_uring_cqe **cqe_ptr, struct __kernel_timespec *ts)` |
| `ref-liburing/completion.rst:103-114` | `c:function` | `int io_uring_peek_cqe(struct io_uring *ring, struct io_uring_cqe **cqe_ptr)` |
| `ref-liburing/completion.rst:118-130` | `c:function` | `unsigned io_uring_peek_batch_cqe(struct io_uring *ring, struct io_uring_cqe **cqes, unsigned count)` |
| `ref-liburing/completion.rst:134-144` | `c:function` | `void *io_uring_cqe_get_data(const struct io_uring_cqe *cqe)` |
| `ref-liburing/completion.rst:148-155` | `c:function` | `void io_uring_cqe_seen(struct io_uring *ring, struct io_uring_cqe *cqe)` |
| `ref-liburing/completion.rst:159-161` | `c:function` | `unsigned io_uring_cq_ready(struct io_uring *ring)` |
| `ref-liburing/cqe.rst:12-18` | `code-block` | `c` |
| `ref-liburing/setup_teardown.rst:9-9` | `c:struct` | `io_uring` |
| `ref-liburing/setup_teardown.rst:10-17` | `code-block` | `c` |
| `ref-liburing/setup_teardown.rst:24-24` | `c:struct` | `io_uring_sq` |
| `ref-liburing/setup_teardown.rst:25-42` | `code-block` | `c` |
| `ref-liburing/setup_teardown.rst:46-46` | `c:struct` | `io_uring_cq` |
| `ref-liburing/setup_teardown.rst:47-59` | `code-block` | `c` |
| `ref-liburing/setup_teardown.rst:63-76` | `c:function` | `int io_uring_queue_init(unsigned entries, struct io_uring *ring, unsigned flags)` |
| `ref-liburing/setup_teardown.rst:80-86` | `c:function` | `int io_uring_queue_init_params(unsigned entries, struct io_uring *ring, struct io_uring_params *p)` |
| `ref-liburing/setup_teardown.rst:90-100` | `c:function` | `int io_uring_queue_mmap(int fd, struct io_uring_params *p, struct io_uring *ring)` |
| `ref-liburing/setup_teardown.rst:104-114` | `c:function` | `int io_uring_ring_dontfork(struct io_uring *ring)` |
| `ref-liburing/setup_teardown.rst:118-124` | `c:function` | `void io_uring_queue_exit(struct io_uring *ring)` |
| `ref-liburing/sqe.rst:13-60` | `code-block` | `c` |
| `ref-liburing/submission.rst:12-22` | `code-block` | `c` |
| `ref-liburing/submission.rst:32-47` | `c:function` | `struct io_uring_sqe *io_uring_get_sqe(struct io_uring *ring)` |
| `ref-liburing/submission.rst:51-58` | `c:function` | `void io_uring_sqe_set_data(struct io_uring_sqe *sqe, void *data)` |
| `ref-liburing/submission.rst:62-69` | `c:function` | `void io_uring_sqe_set_flags(struct io_uring_sqe *sqe, unsigned flags)` |
| `ref-liburing/submission.rst:73-85` | `c:function` | `int io_uring_submit(struct io_uring *ring)` |
| `ref-liburing/submission.rst:89-97` | `c:function` | `int io_uring_submit_and_wait(struct io_uring *ring, unsigned wait_nr)` |
| `ref-liburing/submission.rst:114-120` | `c:function` | `void io_uring_prep_nop(struct io_uring_sqe *sqe)` |
| `ref-liburing/submission.rst:127-141` | `c:function` | `void io_uring_prep_read(struct io_uring_sqe *sqe, int fd, void *buf, unsigned nbytes, off_t offset)` |
| `ref-liburing/submission.rst:148-162` | `c:function` | `void io_uring_prep_write(struct io_uring_sqe *sqe, int fd, const void *buf, unsigned nbytes, off_t offset)` |
| `ref-liburing/submission.rst:169-183` | `c:function` | `void io_uring_prep_readv(struct io_uring_sqe *sqe, int fd, const struct iovec *iovecs, unsigned nr_vecs, off_t offset)` |
| `ref-liburing/submission.rst:190-206` | `c:function` | `void io_uring_prep_read_fixed(struct io_uring_sqe *sqe, int fd, void *buf, unsigned nbytes, off_t offset, int buf_index)` |
| `ref-liburing/submission.rst:213-227` | `c:function` | `void io_uring_prep_writev(struct io_uring_sqe *sqe, int fd, const struct iovec *iovecs, unsigned nr_vecs, off_t offset)` |
| `ref-liburing/submission.rst:234-252` | `c:function` | `void io_uring_prep_write_fixed(struct io_uring_sqe *sqe, int fd, const void *buf, unsigned nbytes, off_t offset, int buf_index)` |
| `ref-liburing/submission.rst:259-276` | `c:function` | `void io_uring_prep_fsync(struct io_uring_sqe *sqe, int fd, unsigned fsync_flags)` |
| `ref-liburing/submission.rst:283-293` | `c:function` | `void io_uring_prep_close(struct io_uring_sqe *sqe, int fd)` |
| `ref-liburing/submission.rst:300-314` | `c:function` | `void io_uring_prep_openat(struct io_uring_sqe *sqe, int dfd, const char *path, int flags, mode_t mode)` |
| `ref-liburing/submission.rst:321-334` | `c:function` | `void io_uring_prep_openat2(struct io_uring_sqe *sqe, int dfd, const char *path, struct open_how *how)` |
| `ref-liburing/submission.rst:341-354` | `c:function` | `void io_uring_prep_fallocate(struct io_uring_sqe *sqe, int fd, int mode, off_t offset, off_t len)` |
| `ref-liburing/submission.rst:361-373` | `c:function` | `void io_uring_prep_statx(struct io_uring_sqe *sqe, int dfd, const char *path, int flags, unsigned mask, struct statx *statxbuf)` |
| `ref-liburing/submission.rst:380-392` | `c:function` | `void io_uring_prep_fadvise(struct io_uring_sqe *sqe, int fd, off_t offset, off_t len, int advice)` |
| `ref-liburing/submission.rst:399-410` | `c:function` | `void io_uring_prep_madvise(struct io_uring_sqe *sqe, void *addr, off_t length, int advice)` |
| `ref-liburing/submission.rst:418-435` | `c:function` | `void io_uring_prep_splice(struct io_uring_sqe *sqe, int fd_in, loff_t off_in, int fd_out, loff_t off_out, unsigned int nbytes, unsigned int splice_flags)` |
| `ref-liburing/submission.rst:442-454` | `c:function` | `void io_uring_prep_recvmsg(struct io_uring_sqe *sqe, int fd, struct msghdr *msg, unsigned flags)` |
| `ref-liburing/submission.rst:461-466` | `c:function` | `void io_uring_prep_sendmsg(struct io_uring_sqe *sqe, int fd, const struct msghdr *msg, unsigned flags)` |
| `ref-liburing/submission.rst:473-486` | `c:function` | `void io_uring_prep_recv(struct io_uring_sqe *sqe, int sockfd, void *buf, size_t len, int flags)` |
| `ref-liburing/submission.rst:493-498` | `c:function` | `void io_uring_prep_send(struct io_uring_sqe *sqe, int sockfd, const void *buf, size_t len, int flags)` |
| `ref-liburing/submission.rst:505-518` | `c:function` | `void io_uring_prep_accept(struct io_uring_sqe *sqe, int fd, struct sockaddr *addr, socklen_t *addrlen, int flags)` |
| `ref-liburing/submission.rst:525-537` | `c:function` | `void io_uring_prep_connect(struct io_uring_sqe *sqe, int fd, struct sockaddr *addr, socklen_t addrlen)` |
| `ref-liburing/submission.rst:544-558` | `c:function` | `void io_uring_prep_epoll_ctl(struct io_uring_sqe *sqe, int epfd, int fd, int op, struct epoll_event *ev)` |
| `ref-liburing/submission.rst:565-576` | `c:function` | `void io_uring_prep_poll_add(struct io_uring_sqe *sqe, int fd, short poll_mask)` |
| `ref-liburing/submission.rst:583-593` | `c:function` | `void io_uring_prep_poll_remove(struct io_uring_sqe *sqe, void *user_data)` |
| `ref-liburing/supported_caps.rst:7-7` | `c:struct` | `io_uring_probe` |
| `ref-liburing/supported_caps.rst:8-16` | `code-block` | `c` |
| `ref-liburing/supported_caps.rst:20-20` | `c:struct` | `io_uring_probe_op` |
| `ref-liburing/supported_caps.rst:21-28` | `code-block` | `c` |
| `ref-liburing/supported_caps.rst:35-44` | `c:function` | `struct io_uring_probe *io_uring_get_probe_ring(struct io_uring *ring)` |
| `ref-liburing/supported_caps.rst:51-58` | `c:function` | `struct io_uring_probe *io_uring_get_probe(void)` |
| `ref-liburing/supported_caps.rst:69-78` | `c:function` | `int io_uring_opcode_supported(struct io_uring_probe *p, int op)` |
| `ref-liburing/supported_caps.rst:85-95` | `c:function` | `int io_uring_register_probe(struct io_uring *ring, struct io_uring_probe *p, unsigned nr)` |
| `tutorial/cat_liburing.rst:7-173` | `code-block` | `c` |
| `tutorial/cat_liburing.rst:182-184` | `code-block` | `c` |
| `tutorial/cat_liburing.rst:188-197` | `code-block` | `c` |
| `tutorial/cat_liburing.rst:201-205` | `code-block` | `c` |
| `tutorial/cp_liburing.rst:10-255` | `code-block` | `c` |
| `tutorial/fixed_buffers.rst:8-126` | `code-block` | `c` |
| `tutorial/link_liburing.rst:8-85` | `code-block` | `c` |
| `tutorial/link_liburing.rst:106-108` | `code-block` | `c` |
| `tutorial/link_liburing.rst:112-114` | `code-block` | `c` |
| `tutorial/probe_liburing.rst:7-68` | `code-block` | `c` |
| `tutorial/register_eventfd.rst:9-110` | `code-block` | `c` |
| `tutorial/sq_poll.rst:20-166` | `code-block` | `c` |
| `tutorial/webserver_liburing.rst:18-465` | `code-block` | `c` |
| `tutorial/webserver_liburing.rst:490-533` | `code-block` | `c` |
| `tutorial/webserver_liburing.rst:537-549` | `code-block` | `c` |
| `tutorial/webserver_liburing.rst:553-560` | `code-block` | `c` |
| `tutorial/webserver_liburing.rst:568-574` | `code-block` | `c` |
| `tutorial/webserver_liburing.rst:578-593` | `code-block` | `c` |
| `tutorial/webserver_liburing.rst:597-607` | `code-block` | `c` |
| `tutorial/webserver_liburing.rst:611-619` | `code-block` | `c` |
| `tutorial/webserver_liburing.rst:623-632` | `code-block` | `c` |
| `tutorial/webserver_liburing.rst:636-644` | `code-block` | `c` |
