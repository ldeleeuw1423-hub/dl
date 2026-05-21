import React from "react";
import { Table, TableHead, TableBody, Th, Td, Tr } from "@/components/ui/Table";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { formatDate, getPermitStatusLabel } from "@/lib/utils";
import { Pencil, Trash2 } from "lucide-react";
import type { Permit, PermitStatus } from "@/types";

interface PermitListProps {
  permits: Permit[];
  onEdit?: (permit: Permit) => void;
  onDelete?: (permitId: string) => void;
}

const statusVariant: Record<PermitStatus, "neutral" | "info" | "warning" | "success" | "danger"> = {
  required: "neutral",
  in_preparation: "info",
  submitted: "warning",
  approved: "success",
  rejected: "danger",
  not_required: "neutral",
};

const riskLevelVariant: Record<string, "danger" | "warning" | "info" | "success"> = {
  critical: "danger",
  high: "warning",
  medium: "info",
  low: "success",
};

const riskLevelLabel: Record<string, string> = {
  critical: "Kritiek",
  high: "Hoog",
  medium: "Gemiddeld",
  low: "Laag",
};

const authorityLabel: Record<string, string> = {
  gemeente: "Gemeente",
  provincie: "Provincie",
  waterschap: "Waterschap",
  prorail: "ProRail",
  rws: "Rijkswaterstaat",
  overig: "Overig",
};

export function PermitList({ permits, onEdit, onDelete }: PermitListProps) {
  if (permits.length === 0) {
    return (
      <div className="text-center py-8 text-sm text-gray-400">
        Geen vergunningen geregistreerd
      </div>
    );
  }

  return (
    <Table>
      <TableHead>
        <tr>
          <Th>Type vergunning</Th>
          <Th>Bevoegd gezag</Th>
          <Th>Status</Th>
          <Th>Risico</Th>
          <Th>Verwachte verlening</Th>
          <Th>Kans vertraging</Th>
          <Th>Eigenaar</Th>
          {(onEdit || onDelete) && <Th />}
        </tr>
      </TableHead>
      <TableBody>
        {permits.map((permit) => (
          <Tr key={permit.id}>
            <Td>
              <div>
                <p className="font-medium text-gray-900">{permit.permit_type}</p>
                {permit.auto_detected && (
                  <span className="text-2xs text-blue-500">Auto-detected</span>
                )}
              </div>
            </Td>
            <Td>{authorityLabel[permit.authority] ?? permit.authority}</Td>
            <Td>
              <Badge variant={statusVariant[permit.status as PermitStatus] ?? "neutral"}>
                {getPermitStatusLabel(permit.status)}
              </Badge>
            </Td>
            <Td>
              <Badge variant={riskLevelVariant[permit.risk_level] ?? "info"}>
                {riskLevelLabel[permit.risk_level] ?? permit.risk_level}
              </Badge>
            </Td>
            <Td>{formatDate(permit.expected_approval)}</Td>
            <Td>
              {permit.delay_probability != null ? (
                <span
                  className={
                    permit.delay_probability >= 50
                      ? "text-red-600 font-medium"
                      : permit.delay_probability >= 25
                      ? "text-amber-600"
                      : "text-green-600"
                  }
                >
                  {permit.delay_probability}%
                </span>
              ) : (
                "—"
              )}
            </Td>
            <Td>{permit.owner ?? "—"}</Td>
            {(onEdit || onDelete) && (
              <Td>
                <div className="flex items-center gap-1">
                  {onEdit && (
                    <Button
                      variant="ghost"
                      size="xs"
                      icon={<Pencil className="h-3 w-3" />}
                      onClick={() => onEdit(permit)}
                    />
                  )}
                  {onDelete && (
                    <Button
                      variant="ghost"
                      size="xs"
                      icon={<Trash2 className="h-3 w-3" />}
                      className="text-red-500 hover:text-red-700 hover:bg-red-50"
                      onClick={() => onDelete(permit.id)}
                    />
                  )}
                </div>
              </Td>
            )}
          </Tr>
        ))}
      </TableBody>
    </Table>
  );
}
