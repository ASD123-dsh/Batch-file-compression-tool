"""
图片压缩模块
负责图片文件的压缩处理
"""
import os
import shutil
import logging
from PIL import Image


class ImageCompressor:
    """图片压缩器"""
    
    def __init__(self, config_manager, logger=None):
        """
        初始化图片压缩器
        
        Args:
            config_manager: 配置管理器实例
            logger: 日志记录器
        """
        self.config = config_manager
        self.logger = logger or logging.getLogger('FileCompressor.ImageCompressor')
    
    def compress(self, source_path, target_path):
        """
        压缩图片文件
        
        Args:
            source_path: 源文件路径
            target_path: 目标文件路径
            
        Returns:
            True如果成功，False如果失败
        """
        try:
            # 验证路径
            normalized_source = self._normalize_path(source_path)
            if not normalized_source or not os.path.isfile(normalized_source):
                raise FileNotFoundError(f"源文件不存在: {source_path}")
            
            normalized_target = self._normalize_path(os.path.dirname(target_path))
            if not normalized_target:
                raise ValueError(f"无效的目标路径: {target_path}")
            
            # 确保目标目录存在
            target_dir = os.path.dirname(target_path)
            os.makedirs(target_dir, exist_ok=True)
            
            photo_quality = self._clamp_int(self.config.get('photo_quality', 85), 0, 100)
            max_width = self.config.get('max_photo_width', 2000)
            max_height = self.config.get('max_photo_height', 2000)
            image_preset = self._get_image_preset()
            target_ext = os.path.splitext(target_path)[1].lower()
            
            with Image.open(normalized_source) as img:
                # 调整图片大小（保持原始比例）
                img = self._resize_if_needed(img, max_width, max_height)
                self._save_image(img, target_path, target_ext, photo_quality, image_preset)
                
            return True
                
        except (FileNotFoundError, PermissionError, OSError) as e:
            self.logger.error(f"压缩图片出错: {source_path}, 错误类型: {type(e).__name__}, 错误: {str(e)}")
            # 如果压缩失败，直接复制原文件
            try:
                shutil.copy2(source_path, target_path)
                return False  # 返回False表示压缩失败但已复制
            except Exception as copy_error:
                self.logger.error(f"复制原始文件失败: {source_path}, 错误: {str(copy_error)}")
                raise
        except (ValueError, Image.UnidentifiedImageError, Image.DecompressionBombError) as e:
            self.logger.error(f"图片格式错误或损坏: {source_path}, 错误类型: {type(e).__name__}, 错误: {str(e)}")
            # 如果压缩失败，直接复制原文件
            try:
                shutil.copy2(source_path, target_path)
                return False
            except Exception as copy_error:
                self.logger.error(f"复制原始文件失败: {source_path}, 错误: {str(copy_error)}")
                raise
        except Exception as e:
            self.logger.error(f"压缩图片时发生未知错误: {source_path}, 错误类型: {type(e).__name__}, 错误: {str(e)}")
            try:
                shutil.copy2(source_path, target_path)
                return False
            except Exception as copy_error:
                self.logger.error(f"复制原始文件失败: {source_path}, 错误: {str(copy_error)}")
                raise
    
    @staticmethod
    def _normalize_path(path):
        """规范化路径"""
        if not path:
            return None
        try:
            from pathlib import Path
            normalized = Path(path).resolve()
            path_str = str(normalized)
            if '..' in path_str or path_str.startswith('\\\\'):
                return None
            return str(normalized)
        except (ValueError, OSError):
            return None

    @staticmethod
    def _clamp_int(value, min_value, max_value):
        try:
            value_int = int(value)
        except Exception:
            value_int = min_value
        return max(min_value, min(max_value, value_int))

    def _get_image_preset(self):
        preset = self.config.get('image_preset', '自定义')
        if preset not in ['自定义', '压缩优先', '清晰优先']:
            return '自定义'
        return preset

    @staticmethod
    def _resize_if_needed(img, max_width, max_height):
        width, height = img.size
        if width > max_width or height > max_height:
            ratio = min(max_width / width, max_height / height)
            new_width = int(width * ratio)
            new_height = int(height * ratio)
            return img.resize((new_width, new_height), Image.LANCZOS)
        return img

    def _save_image(self, img, target_path, target_ext, photo_quality, image_preset):
        if target_ext in ['.jpg', '.jpeg']:
            self._save_jpeg(img, target_path, photo_quality, image_preset)
            return
        if target_ext == '.png':
            self._save_png(img, target_path, photo_quality, image_preset)
            return
        if target_ext == '.webp':
            self._save_webp(img, target_path, photo_quality, image_preset)
            return
        img.save(target_path, optimize=True)

    @staticmethod
    def _convert_for_jpeg(img):
        if img.mode == 'RGB':
            return img
        if img.mode in ['RGBA', 'LA'] or (img.mode == 'P' and 'transparency' in img.info):
            rgba = img.convert('RGBA')
            background = Image.new('RGB', rgba.size, (255, 255, 255))
            background.paste(rgba, mask=rgba.split()[-1])
            return background
        return img.convert('RGB')

    def _convert_for_png24(self, img):
        if img.mode == 'RGB':
            return img

        if img.mode in ['RGBA', 'LA'] or (img.mode == 'P' and 'transparency' in img.info) or ('transparency' in img.info):
            rgba = img.convert('RGBA')
            try:
                alpha = rgba.getchannel('A')
                alpha_min, alpha_max = alpha.getextrema()
            except Exception:
                alpha_min, alpha_max = 0, 255

            if alpha_min == 255 and alpha_max == 255:
                self.logger.info(f"PNG-24转换: size={img.size}, src_mode={img.mode}, alpha=opaque, dst_mode=RGB")
                return rgba.convert('RGB')

            background = Image.new('RGBA', rgba.size, (255, 255, 255, 255))
            composited = Image.alpha_composite(background, rgba)
            self.logger.info(f"PNG-24转换: size={img.size}, src_mode={img.mode}, alpha=composite_white, dst_mode=RGB")
            return composited.convert('RGB')

        self.logger.info(f"PNG-24转换: size={img.size}, src_mode={img.mode}, dst_mode=RGB")
        return img.convert('RGB')

    def _save_jpeg(self, img, target_path, photo_quality, image_preset):
        if image_preset == '压缩优先':
            quality = min(photo_quality, 75)
        elif image_preset == '清晰优先':
            quality = max(photo_quality, 92)
        else:
            quality = photo_quality

        save_img = self._convert_for_jpeg(img)
        save_img.save(target_path, quality=quality, optimize=True, progressive=True)

    def _save_webp(self, img, target_path, photo_quality, image_preset):
        if image_preset == '压缩优先':
            quality = min(photo_quality, 70)
        elif image_preset == '清晰优先':
            quality = max(photo_quality, 90)
        else:
            quality = photo_quality

        img.save(target_path, quality=quality, method=6)

    def _save_png(self, img, target_path, photo_quality, image_preset):
        if image_preset == '清晰优先':
            compress_level = 6
            save_img = img
        elif image_preset == '压缩优先':
            compress_level = 9
            save_img = self._convert_for_png24(img)
            self.logger.info(f"PNG-24压缩优先: size={img.size}, src_mode={img.mode}, dst_mode={getattr(save_img, 'mode', 'unknown')}")
        else:
            if photo_quality >= 90:
                compress_level = 6
                save_img = img
            elif photo_quality >= 70:
                compress_level = 9
                save_img = img
            else:
                compress_level = 9
                colors = int(round(16 + (photo_quality / 70.0) * (256 - 16)))
                colors = max(16, min(256, colors))
                save_img = self._maybe_quantize_png(img, colors, Image.NONE)

        save_img.save(target_path, optimize=True, compress_level=compress_level)

    def _should_quantize_png(self, img):
        try:
            if img.mode == 'P':
                return False

            check_img = img
            if check_img.mode not in ['RGB', 'RGBA']:
                check_img = check_img.convert('RGBA')

            colors = check_img.getcolors(maxcolors=257)
            if colors is None:
                self.logger.info(f"PNG-8判定: size={check_img.size}, mode={check_img.mode}, colors=>256, quantize=False")
                return False
            color_count = len(colors)
            should_quantize = color_count <= 256
            self.logger.info(f"PNG-8判定: size={check_img.size}, mode={check_img.mode}, colors={color_count}, quantize={should_quantize}")
            return should_quantize
        except Exception:
            return False

    def _maybe_quantize_png(self, img, colors, dither_mode):
        try:
            if img.mode == 'P':
                return img
            if img.mode not in ['RGB', 'RGBA']:
                img = img.convert('RGBA')
            try:
                quantized = img.convert('P', palette=Image.ADAPTIVE, colors=colors, dither=dither_mode)
                self.logger.info(f"PNG-8量化: colors={colors}, dither={self._dither_to_text(dither_mode)}, method=ADAPTIVE_CONVERT, dst_mode={quantized.mode}")
                return quantized
            except Exception:
                method = Image.MEDIANCUT if img.mode == 'RGB' else Image.FASTOCTREE
                quantized = img.quantize(colors=colors, method=method, dither=dither_mode)
                self.logger.info(f"PNG-8量化: colors={colors}, dither={self._dither_to_text(dither_mode)}, method={'MEDIANCUT' if method == Image.MEDIANCUT else 'FASTOCTREE'}, dst_mode={quantized.mode}")
                return quantized
        except Exception as e:
            self.logger.debug(f"PNG颜色量化失败，回退为无损压缩: {e}")
            return img

    def _should_accept_png8(self, original_img, png8_img):
        try:
            original_rgba, png8_rgba = self._prepare_compare_images(original_img, png8_img)
            mae, high_pct = self._compute_image_diff_stats(original_rgba, png8_rgba)

            accept = True
            if mae > 6.0:
                accept = False
            if high_pct > 2.0:
                accept = False

            return {
                'accept': accept,
                'mae': mae,
                'high_pct': high_pct
            }
        except Exception as e:
            self.logger.debug(f"PNG-8质量评估失败，回退为无损压缩: {e}")
            return {
                'accept': False,
                'mae': 999.0,
                'high_pct': 100.0
            }

    @staticmethod
    def _prepare_compare_images(original_img, png8_img):
        max_sample = 256

        a = original_img.convert('RGBA') if original_img.mode != 'RGBA' else original_img
        b = png8_img.convert('RGBA') if png8_img.mode != 'RGBA' else png8_img

        if a.size != b.size:
            b = b.resize(a.size, Image.NEAREST)

        width, height = a.size
        if width > max_sample or height > max_sample:
            ratio = min(max_sample / float(width), max_sample / float(height))
            new_width = max(1, int(width * ratio))
            new_height = max(1, int(height * ratio))
            a = a.resize((new_width, new_height), Image.BILINEAR)
            b = b.resize((new_width, new_height), Image.BILINEAR)

        return a, b

    @staticmethod
    def _compute_image_diff_stats(img_a_rgba, img_b_rgba):
        data_a = list(img_a_rgba.getdata())
        data_b = list(img_b_rgba.getdata())
        total = min(len(data_a), len(data_b))
        if total <= 0:
            return 0.0, 0.0

        sum_abs = 0
        high_count = 0
        for i in range(total):
            pa = data_a[i]
            pb = data_b[i]
            dr = abs(pa[0] - pb[0])
            dg = abs(pa[1] - pb[1])
            db = abs(pa[2] - pb[2])
            da = abs(pa[3] - pb[3])
            sum_abs += (dr + dg + db + da)
            if dr > 24 or dg > 24 or db > 24 or da > 24:
                high_count += 1

        mae = float(sum_abs) / float(total * 4)
        high_pct = float(high_count) * 100.0 / float(total)
        return mae, high_pct

    @staticmethod
    def _dither_to_text(dither_mode):
        if dither_mode == Image.FLOYDSTEINBERG:
            return 'FLOYDSTEINBERG'
        if dither_mode == Image.NONE:
            return 'NONE'
        return str(dither_mode)

