package com.karandaev.roadCrackDetectionServer.service;

import com.karandaev.roadCrackDetectionServer.image.ImageSecurityProperties;
import com.karandaev.roadCrackDetectionServer.image.ImageValidationException;
import com.karandaev.roadCrackDetectionServer.image.MagicBytesSniffer;
import com.karandaev.roadCrackDetectionServer.image.SafeImage;
import com.karandaev.roadCrackDetectionServer.image.antivirus.VirusScanner;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;

import javax.imageio.*;
import javax.imageio.stream.ImageInputStream;
import java.awt.*;
import java.awt.image.BufferedImage;
import java.io.*;
import java.util.Iterator;
import java.util.Locale;

@Service
public class ImageValidationService {

  private final ImageSecurityProperties props;
  private final VirusScanner virusScanner;
  private final MagicBytesSniffer sniffer = new MagicBytesSniffer();

  public ImageValidationService(ImageSecurityProperties props, VirusScanner virusScanner) {
    this.props = props;
    this.virusScanner = virusScanner;
  }

  public SafeImage validateAndNormalize(byte[] bytes) {
    if (bytes == null || bytes.length == 0) {
      throw new ImageValidationException(HttpStatus.BAD_REQUEST, "Empty file");
    }
    if (bytes.length > props.getMaxBytes()) {
      throw new ImageValidationException(HttpStatus.PAYLOAD_TOO_LARGE, "File too large");
    }

    // Антивирус (опционально)
    virusScanner.scanOrThrow(bytes);

    // Формат по magic bytes
    var fmtOpt = sniffer.sniff(bytes);
    if (fmtOpt.isEmpty()) {
      throw new ImageValidationException(
          HttpStatus.UNSUPPORTED_MEDIA_TYPE, "Unknown file signature");
    }

    String imageIoFormatName = fmtOpt.get().imageIoName(); // JPEG/PNG/WEBP...
    if (props.getAllowedFormats().stream().noneMatch(a -> a.equalsIgnoreCase(imageIoFormatName))) {
      throw new ImageValidationException(
          HttpStatus.UNSUPPORTED_MEDIA_TYPE, "Format not allowed: " + imageIoFormatName);
    }

    // Узнаем размеры без полной декомпрессии
    Dimension dim = probeDimensions(bytes);
    int w = dim.width;
    int h = dim.height;

    if (w <= 0 || h <= 0) {
      throw new ImageValidationException(
          HttpStatus.UNSUPPORTED_MEDIA_TYPE, "Invalid image dimensions");
    }
    if (w > props.getMaxWidth() || h > props.getMaxHeight()) {
      throw new ImageValidationException(
          HttpStatus.PAYLOAD_TOO_LARGE, "Image dimensions too large");
    }
    long pixels = (long) w * (long) h;
    long maxPixels = (long) props.getMaxMegapixels() * 1_000_000L;
    if (pixels > maxPixels) {
      throw new ImageValidationException(
          HttpStatus.PAYLOAD_TOO_LARGE, "Image megapixels too large");
    }

    // Полная декодировка (после лимитов по размерам это уже безопаснее)
    BufferedImage img = decode(bytes);

    // Нормализация: рисуем в новый буфер и пересохраняем (убираем метаданные/странные секции)
    String outFormat = props.getNormalizeFormat().toUpperCase(Locale.ROOT);
    byte[] normalized = normalize(img, outFormat);

    return new SafeImage(normalized, img.getWidth(), img.getHeight(), outFormat);
  }

  private Dimension probeDimensions(byte[] bytes) {
    try (ImageInputStream iis = ImageIO.createImageInputStream(new ByteArrayInputStream(bytes))) {
      if (iis == null) {
        throw new ImageValidationException(
            HttpStatus.UNSUPPORTED_MEDIA_TYPE, "Cannot read image stream");
      }
      Iterator<ImageReader> readers = ImageIO.getImageReaders(iis);
      if (!readers.hasNext()) {
        throw new ImageValidationException(
            HttpStatus.UNSUPPORTED_MEDIA_TYPE, "No ImageReader for this format");
      }
      ImageReader reader = readers.next();
      try {
        reader.setInput(iis, true, true);
        int w = reader.getWidth(0);
        int h = reader.getHeight(0);
        return new Dimension(w, h);
      } finally {
        reader.dispose();
      }
    } catch (IOException e) {
      throw new ImageValidationException(
          HttpStatus.UNSUPPORTED_MEDIA_TYPE, "Corrupted image header");
    }
  }

  private BufferedImage decode(byte[] bytes) {
    try (ByteArrayInputStream in = new ByteArrayInputStream(bytes)) {
      BufferedImage img = ImageIO.read(in);
      if (img == null) {
        throw new ImageValidationException(
            HttpStatus.UNSUPPORTED_MEDIA_TYPE, "Image cannot be decoded");
      }
      return img;
    } catch (IOException e) {
      throw new ImageValidationException(
          HttpStatus.UNSUPPORTED_MEDIA_TYPE, "Failed to decode image");
    }
  }

  private byte[] normalize(BufferedImage src, String outFormat) {
    // Создаём “чистую” картинку без привязки к исходным цветовым моделям/метаданным
    int type =
        outFormat.equals("JPEG") ? BufferedImage.TYPE_3BYTE_BGR : BufferedImage.TYPE_INT_ARGB;
    BufferedImage clean = new BufferedImage(src.getWidth(), src.getHeight(), type);

    Graphics2D g = clean.createGraphics();
    try {
      // Рисуем исходник в новый буфер
      g.drawImage(src, 0, 0, null);
    } finally {
      g.dispose();
    }

    try (ByteArrayOutputStream out = new ByteArrayOutputStream()) {
      // Для JPEG можно выставлять качество через ImageWriteParam, но оставим дефолт для простоты
      boolean ok = ImageIO.write(clean, outFormat, out);
      if (!ok) {
        throw new ImageValidationException(
            HttpStatus.UNSUPPORTED_MEDIA_TYPE, "Cannot write normalized image");
      }
      return out.toByteArray();
    } catch (IOException e) {
      throw new ImageValidationException(HttpStatus.INTERNAL_SERVER_ERROR, "Normalization failed");
    }
  }
}
