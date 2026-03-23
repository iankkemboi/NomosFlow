import { Zap, Flame, Battery } from "lucide-react";
import { cn } from "@/lib/utils";

interface DeviceIconProps {
  deviceType: string;
  className?: string;
  size?: number;
}

export default function DeviceIcon({ deviceType, className, size = 16 }: DeviceIconProps) {
  const props = { size, className };
  switch (deviceType) {
    case "ev":        return <Zap {...props} />;
    case "heat_pump": return <Flame {...props} />;
    case "battery":   return <Battery {...props} />;
    default:          return <Zap {...props} />;
  }
}
