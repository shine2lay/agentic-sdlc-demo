/**
 * Legend component for the DAG view.
 * Displays color explanations for stage statuses and edge types.
 */
import { STATUS_COLORS, STATUS_BG_COLORS, EDGE_COLORS } from '../../constants';

export function DagLegend() {
  return (
    <div className="bg-[var(--temper-panel)] border border-[var(--temper-border)] rounded-lg p-4">
      <h3 className="text-sm font-semibold text-[var(--temper-text)] mb-3">
        Pipeline Stage Legend
      </h3>
      
      {/* Status Colors */}
      <div className="mb-4">
        <h4 className="text-xs font-medium text-[var(--temper-text-muted)] mb-2">
          Stage Status
        </h4>
        <div className="flex flex-wrap gap-4">
          <div className="flex items-center gap-2">
            <span
              className="w-3 h-3 rounded-full"
              style={{ backgroundColor: STATUS_COLORS.completed }}
            />
            <span className="text-xs text-[var(--temper-text)]">
              Completed
            </span>
          </div>
          <div className="flex items-center gap-2">
            <span
              className="w-3 h-3 rounded-full"
              style={{ backgroundColor: STATUS_COLORS.running }}
            />
            <span className="text-xs text-[var(--temper-text)]">
              Running
            </span>
          </div>
          <div className="flex items-center gap-2">
            <span
              className="w-3 h-3 rounded-full"
              style={{ backgroundColor: STATUS_COLORS.failed }}
            />
            <span className="text-xs text-[var(--temper-text)]">
              Failed
            </span>
          </div>
          <div className="flex items-center gap-2">
            <span
              className="w-3 h-3 rounded-full"
              style={{ backgroundColor: STATUS_COLORS.pending }}
            />
            <span className="text-xs text-[var(--temper-text)]">
              Pending
            </span>
          </div>
        </div>
      </div>

      {/* Edge Types */}
      <div>
        <h4 className="text-xs font-medium text-[var(--temper-text-muted)] mb-2">
          Edge Types
        </h4>
        <div className="flex flex-wrap gap-4">
          <div className="flex items-center gap-2">
            <span
              className="w-3 h-0.5"
              style={{ backgroundColor: EDGE_COLORS.dataFlow }}
            />
            <span className="text-xs text-[var(--temper-text)]">
              Data Flow
            </span>
          </div>
          <div className="flex items-center gap-2">
            <span
              className="w-3 h-0.5"
              style={{ backgroundColor: EDGE_COLORS.loopBack }}
            />
            <span className="text-xs text-[var(--temper-text)]">
              Loop Back
            </span>
          </div>
          <div className="flex items-center gap-2">
            <span
              className="w-3 h-0.5"
              style={{ backgroundColor: EDGE_COLORS.collaboration }}
            />
            <span className="text-xs text-[var(--temper-text)]">
              Collaboration
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
