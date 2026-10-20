// CordDesk desktop look: sidebar, cards, gradient buttons and illustrations
// used by the home page.

import 'package:flutter/material.dart';
import 'package:get/get.dart';

import '../../common.dart';
import '../../models/platform_model.dart';

/// Lets the "Start a new connection" button focus the remote ID field.
FocusNode? cordRemoteIdFocusNode;

class CordColors {
  static const blue = Color(0xFF1F5EFF);
  static const blueLight = Color(0xFF2E9BFF);
  static const purple = Color(0xFF8B5CF6);
  static const navyTop = Color(0xFF0A1433);
  static const navyBottom = Color(0xFF0B1F5C);
  static const textDark = Color(0xFF0F172A);
  static const textMuted = Color(0xFF5B6478);

  static const buttonGradient = LinearGradient(
    begin: Alignment.centerLeft,
    end: Alignment.centerRight,
    colors: [Color(0xFF1D4FF2), Color(0xFF2A8CFF), Color(0xFF34B4FF)],
  );

  static bool isDark(BuildContext context) =>
      Theme.of(context).brightness == Brightness.dark;

  static Color background(BuildContext context) =>
      isDark(context) ? const Color(0xFF14161C) : const Color(0xFFF2F5FC);

  static Color card(BuildContext context) =>
      isDark(context) ? const Color(0xFF1D2029) : Colors.white;

  static Color border(BuildContext context) =>
      isDark(context) ? const Color(0xFF2B2F3A) : const Color(0xFFE6EBF5);

  static Color title(BuildContext context) =>
      isDark(context) ? Colors.white : textDark;

  static Color muted(BuildContext context) =>
      isDark(context) ? Colors.white60 : textMuted;
}

class CordCard extends StatelessWidget {
  final Widget child;
  final EdgeInsetsGeometry padding;
  final Gradient? gradient;

  const CordCard(
      {Key? key,
      required this.child,
      this.padding = const EdgeInsets.all(24),
      this.gradient})
      : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Container(
      clipBehavior: Clip.antiAlias,
      decoration: BoxDecoration(
        color: gradient == null ? CordColors.card(context) : null,
        gradient: gradient,
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: CordColors.border(context)),
        boxShadow: [
          BoxShadow(
            color: const Color(0xFF1F5EFF).withOpacity(0.06),
            blurRadius: 24,
            offset: const Offset(0, 8),
          ),
        ],
      ),
      padding: padding,
      child: child,
    );
  }
}

/// Rounded square icon button (copy / refresh / dropdown).
class CordIconButton extends StatelessWidget {
  final IconData icon;
  final String tooltip;
  final VoidCallback? onTap;
  final double size;

  const CordIconButton(
      {Key? key,
      required this.icon,
      required this.tooltip,
      this.onTap,
      this.size = 46})
      : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Tooltip(
      message: tooltip,
      child: Material(
        color: CordColors.card(context),
        borderRadius: BorderRadius.circular(12),
        child: InkWell(
          borderRadius: BorderRadius.circular(12),
          onTap: onTap,
          child: Container(
            width: size,
            height: size,
            decoration: BoxDecoration(
              borderRadius: BorderRadius.circular(12),
              border: Border.all(color: CordColors.border(context)),
            ),
            child: Icon(icon, size: 22, color: CordColors.title(context)),
          ),
        ),
      ),
    );
  }
}

class CordGradientButton extends StatelessWidget {
  final IconData icon;
  final String label;
  final VoidCallback? onTap;
  final double height;
  final double fontSize;

  const CordGradientButton(
      {Key? key,
      required this.icon,
      required this.label,
      this.onTap,
      this.height = 56,
      this.fontSize = 18})
      : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Container(
      height: height,
      decoration: BoxDecoration(
        gradient: CordColors.buttonGradient,
        borderRadius: BorderRadius.circular(14),
        boxShadow: [
          BoxShadow(
            color: CordColors.blue.withOpacity(0.35),
            blurRadius: 18,
            offset: const Offset(0, 8),
          ),
        ],
      ),
      child: Material(
        color: Colors.transparent,
        child: InkWell(
          borderRadius: BorderRadius.circular(14),
          onTap: onTap,
          child: Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(icon, color: Colors.white, size: fontSize + 6),
              const SizedBox(width: 14),
              Flexible(
                child: Text(
                  label,
                  overflow: TextOverflow.ellipsis,
                  style: TextStyle(
                      color: Colors.white,
                      fontSize: fontSize,
                      fontWeight: FontWeight.w600),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

/// Dark navy sidebar with logo, Home / Settings and About at the bottom.
class CordSidebar extends StatelessWidget {
  final VoidCallback? onSettings;
  final VoidCallback? onAbout;

  const CordSidebar({Key? key, this.onSettings, this.onAbout})
      : super(key: key);

  @override
  Widget build(BuildContext context) {
    Widget item(IconData icon, String label, VoidCallback? onTap,
        {bool selected = false}) {
      return Container(
        margin: const EdgeInsets.symmetric(horizontal: 12, vertical: 5),
        decoration: selected
            ? BoxDecoration(
                gradient: CordColors.buttonGradient,
                borderRadius: BorderRadius.circular(12),
                boxShadow: [
                  BoxShadow(
                    color: CordColors.blue.withOpacity(0.45),
                    blurRadius: 16,
                    offset: const Offset(0, 6),
                  ),
                ],
              )
            : null,
        child: Material(
          color: Colors.transparent,
          child: InkWell(
            borderRadius: BorderRadius.circular(12),
            onTap: onTap,
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 14),
              child: Row(
                children: [
                  Icon(icon,
                      size: 26,
                      color: selected ? Colors.white : Colors.white70),
                  const SizedBox(width: 12),
                  Flexible(
                    child: Text(
                      label,
                      overflow: TextOverflow.ellipsis,
                      style: TextStyle(
                        color: selected ? Colors.white : Colors.white70,
                        fontSize: 15,
                        fontWeight:
                            selected ? FontWeight.w600 : FontWeight.normal,
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ),
        ),
      );
    }

    return Container(
      width: 168,
      decoration: const BoxDecoration(
        gradient: LinearGradient(
          begin: Alignment.topCenter,
          end: Alignment.bottomCenter,
          colors: [CordColors.navyTop, CordColors.navyBottom],
        ),
      ),
      child: Stack(
        children: [
          Positioned(
            left: -90,
            right: -60,
            bottom: -120,
            height: 360,
            child: Container(
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                gradient: RadialGradient(colors: [
                  CordColors.blueLight.withOpacity(0.45),
                  CordColors.blue.withOpacity(0.12),
                  Colors.transparent,
                ]),
              ),
            ),
          ),
          Column(
            children: [
              const SizedBox(height: 26),
              ClipRRect(
                borderRadius: BorderRadius.circular(14),
                child: loadIcon(56),
              ),
              const SizedBox(height: 10),
              Text(
                bind.mainGetAppNameSync(),
                style: const TextStyle(
                    color: Colors.white,
                    fontSize: 21,
                    fontWeight: FontWeight.w600),
              ),
              const SizedBox(height: 28),
              item(Icons.home_rounded, translate('Home'), () {},
                  selected: true),
              if (onSettings != null)
                item(Icons.settings_rounded, translate('Settings'), onSettings),
              const Spacer(),
              if (onAbout != null)
                InkWell(
                  onTap: onAbout,
                  child: Column(
                    children: [
                      const Icon(Icons.info_outline_rounded,
                          color: Colors.white70, size: 30),
                      const SizedBox(height: 6),
                      Text(translate('About'),
                          style: const TextStyle(
                              color: Colors.white70, fontSize: 15)),
                    ],
                  ).paddingSymmetric(vertical: 8, horizontal: 20),
                ),
              const SizedBox(height: 26),
            ],
          ),
        ],
      ),
    );
  }
}

/// Small monitor illustration for the "Your Desktop" card.
class CordMonitorArt extends StatelessWidget {
  final double width;

  const CordMonitorArt({Key? key, this.width = 84}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    final h = width * 0.62;
    return SizedBox(
      width: width,
      height: h + width * 0.2,
      child: Column(
        children: [
          Container(
            width: width,
            height: h,
            padding: EdgeInsets.all(width * 0.06),
            decoration: BoxDecoration(
              color: const Color(0xFF9CC8FF),
              borderRadius: BorderRadius.circular(width * 0.08),
              boxShadow: [
                BoxShadow(
                    color: CordColors.blue.withOpacity(0.25),
                    blurRadius: 14,
                    offset: const Offset(0, 6)),
              ],
            ),
            child: Container(
              decoration: BoxDecoration(
                borderRadius: BorderRadius.circular(width * 0.04),
                gradient: const LinearGradient(
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                  colors: [Color(0xFFE8F3FF), Color(0xFF7FB2FF)],
                ),
              ),
            ),
          ),
          Container(
              width: width * 0.12, height: width * 0.1, color: const Color(0xFF8DB8F5)),
          Container(
            width: width * 0.42,
            height: width * 0.07,
            decoration: BoxDecoration(
              color: const Color(0xFF8DB8F5),
              borderRadius: BorderRadius.circular(width * 0.04),
            ),
          ),
        ],
      ),
    );
  }
}

/// Laptop + monitor illustration for empty peer lists.
class CordDevicesArt extends StatelessWidget {
  const CordDevicesArt({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    Widget screen(double w, double h, {Widget? child}) => Container(
          width: w,
          height: h,
          padding: const EdgeInsets.all(6),
          decoration: BoxDecoration(
            color: const Color(0xFF7C8DB5),
            borderRadius: BorderRadius.circular(8),
          ),
          child: Container(
            decoration: BoxDecoration(
              borderRadius: BorderRadius.circular(4),
              gradient: const LinearGradient(
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
                colors: [Color(0xFF1E3A8A), Color(0xFF3B82F6)],
              ),
            ),
            child: child,
          ),
        );

    return SizedBox(
      width: 320,
      height: 170,
      child: Stack(
        alignment: Alignment.center,
        children: [
          Positioned(
            bottom: 6,
            child: Container(
              width: 300,
              height: 100,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                gradient: RadialGradient(colors: [
                  CordColors.blueLight.withOpacity(0.18),
                  Colors.transparent,
                ]),
              ),
            ),
          ),
          Positioned(
            right: 30,
            top: 14,
            child: Column(children: [
              screen(100, 72),
              Container(width: 10, height: 14, color: const Color(0xFF9AA8C7)),
              Container(
                  width: 44,
                  height: 6,
                  decoration: BoxDecoration(
                      color: const Color(0xFF9AA8C7),
                      borderRadius: BorderRadius.circular(3))),
            ]),
          ),
          Positioned(
            left: 50,
            bottom: 18,
            child: Column(children: [
              screen(150, 96,
                  child: Center(
                      child: ClipRRect(
                          borderRadius: BorderRadius.circular(8),
                          child: loadIcon(34)))),
              Container(
                width: 184,
                height: 10,
                decoration: BoxDecoration(
                  color: const Color(0xFFB4C0DA),
                  borderRadius: BorderRadius.circular(5),
                ),
              ),
            ]),
          ),
        ],
      ),
    );
  }
}

/// Empty state shown in the peer list tabs.
class CordEmptyPeers extends StatelessWidget {
  final String title;
  final String message;

  const CordEmptyPeers({Key? key, required this.title, required this.message})
      : super(key: key);

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          const CordDevicesArt(),
          const SizedBox(height: 14),
          if (title.isNotEmpty)
            Text(title,
                textAlign: TextAlign.center,
                style: TextStyle(
                    fontSize: 22,
                    fontWeight: FontWeight.w700,
                    color: CordColors.title(context))),
          const SizedBox(height: 8),
          Text(message,
              textAlign: TextAlign.center,
              style: TextStyle(
                  fontSize: 14, height: 1.5, color: CordColors.muted(context))),
          const SizedBox(height: 18),
          Material(
            color: CordColors.blue.withOpacity(0.08),
            borderRadius: BorderRadius.circular(12),
            child: InkWell(
              borderRadius: BorderRadius.circular(12),
              onTap: () => cordRemoteIdFocusNode?.requestFocus(),
              child: Padding(
                padding:
                    const EdgeInsets.symmetric(horizontal: 26, vertical: 14),
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    const Icon(Icons.add_rounded,
                        color: CordColors.blue, size: 24),
                    const SizedBox(width: 10),
                    Text(translate('Start a new connection'),
                        style: const TextStyle(
                            color: CordColors.blue,
                            fontSize: 15,
                            fontWeight: FontWeight.w600)),
                  ],
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}
