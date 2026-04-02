"use client";

/**
 * PipelineMode - Mode 11: Squad pipeline progress display.
 *
 * Shows the active pipeline's steps as a vertical list with status indicators.
 * Each step has a colored circle (green=completed, blue=active, yellow=waiting_approval,
 * red=error, gray=pending) and its name. Active steps pulse via alpha animation.
 */

import { Graphics } from "pixi.js";
import { useState, useEffect, useCallback, type ReactNode } from "react";
import { useSquadStore } from "@/stores/squadStore";
import type { PipelineStepStatus } from "@/types/squads";

export interface PipelineModeProps {
  width?: number;
  height?: number;
}

const MAX_VISIBLE_STEPS = 6;

function getStatusColor(status: PipelineStepStatus | undefined): number {
  switch (status) {
    case "completed":
    case "approved":
      return 0x22c55e; // green
    case "active":
    case "retry":
      return 0x3b82f6; // blue
    case "waiting_approval":
      return 0xf59e0b; // yellow
    case "error":
      return 0xef4444; // red
    default:
      return 0x9ca3af; // gray (pending)
  }
}

function getStatusLabel(status: PipelineStepStatus | undefined): string {
  switch (status) {
    case "completed":
      return "✓";
    case "approved":
      return "✓";
    case "active":
      return "▶";
    case "retry":
      return "↺";
    case "waiting_approval":
      return "?";
    case "error":
      return "✗";
    default:
      return "○";
  }
}

export function PipelineMode({ width = 330, height = 155 }: PipelineModeProps): ReactNode {
  const pipelineState = useSquadStore((s) => s.pipelineState);
  const squads = useSquadStore((s) => s.squads);
  const [pulseAlpha, setPulseAlpha] = useState(1);
  const [scrollOffset, setScrollOffset] = useState(0);

  // Pulse animation for active step
  useEffect(() => {
    let t = 0;
    const interval = setInterval(() => {
      t += 0.1;
      setPulseAlpha(0.4 + 0.6 * (0.5 + 0.5 * Math.sin(t * Math.PI)));
    }, 50);
    return () => clearInterval(interval);
  }, []);

  // Auto-scroll to keep active step visible
  useEffect(() => {
    if (!pipelineState) return;
    const activeIndex = pipelineState.currentStepIndex;
    if (activeIndex < 0) return;
    if (activeIndex >= scrollOffset + MAX_VISIBLE_STEPS) {
      setScrollOffset(Math.max(0, activeIndex - MAX_VISIBLE_STEPS + 1));
    } else if (activeIndex < scrollOffset) {
      setScrollOffset(activeIndex);
    }
  }, [pipelineState?.currentStepIndex, pipelineState, scrollOffset]);

  if (!pipelineState) {
    return (
      <pixiContainer>
        <pixiText
          text="No active pipeline"
          x={width / 2}
          y={height / 2 - 10}
          anchor={0.5}
          style={{
            fontFamily: '"Courier New", monospace',
            fontSize: 11,
            fill: "#9ca3af",
          }}
          resolution={2}
        />
        <pixiText
          text="Waiting for squad..."
          x={width / 2}
          y={height / 2 + 8}
          anchor={0.5}
          style={{
            fontFamily: '"Courier New", monospace',
            fontSize: 10,
            fill: "#6b7280",
          }}
          resolution={2}
        />
      </pixiContainer>
    );
  }

  // Find squad name
  const squad = squads.find((s) => s.code === pipelineState.squadCode);
  const squadName = squad ? squad.name : pipelineState.squadCode;

  // Build step list from stepStates
  const stepIds = Object.keys(pipelineState.stepStates);
  const totalSteps = pipelineState.totalSteps || stepIds.length;
  const visibleSteps = stepIds.slice(scrollOffset, scrollOffset + MAX_VISIBLE_STEPS);
  const stepH = 22;

  return (
    <pixiContainer>
      {/* Squad name subtitle */}
      <pixiText
        text={squadName.slice(0, 32)}
        x={width / 2}
        y={4}
        anchor={0.5}
        style={{
          fontFamily: '"Courier New", monospace',
          fontSize: 10,
          fill: "#6b7280",
        }}
        resolution={2}
      />

      {/* Progress fraction */}
      <pixiText
        text={`${pipelineState.currentStepIndex}/${totalSteps}`}
        x={width - 14}
        y={4}
        anchor={{ x: 1, y: 0 }}
        style={{
          fontFamily: '"Courier New", monospace',
          fontSize: 9,
          fill: "#9ca3af",
        }}
        resolution={2}
      />

      {/* Progress bar background */}
      <pixiGraphics
        draw={useCallback(
          (g: Graphics) => {
            g.clear();
            // Background track
            g.roundRect(14, 18, width - 28, 5, 2);
            g.fill(0xe5e7eb);
            // Filled portion
            const progress =
              totalSteps > 0 ? pipelineState.currentStepIndex / totalSteps : 0;
            if (progress > 0) {
              g.roundRect(14, 18, (width - 28) * progress, 5, 2);
              g.fill(0x22c55e);
            }
          },
          [width, pipelineState.currentStepIndex, totalSteps],
        )}
      />

      {/* Step list */}
      {visibleSteps.map((stepId, i) => {
        const status = pipelineState.stepStates[stepId];
        const isActive = status === "active" || status === "retry";
        const color = getStatusColor(status);
        const label = getStatusLabel(status);
        const y = 28 + i * stepH;
        const alpha = isActive ? pulseAlpha : 1;

        return (
          <pixiContainer key={stepId} y={y} alpha={alpha}>
            {/* Status circle */}
            <pixiGraphics
              draw={useCallback(
                (g: Graphics) => {
                  g.clear();
                  g.circle(22, 7, 6);
                  g.fill(color);
                  if (isActive) {
                    g.circle(22, 7, 6);
                    g.stroke({ width: 1.5, color: 0xffffff });
                  }
                },
                [color, isActive],
              )}
            />
            {/* Status icon */}
            <pixiText
              text={label}
              x={22}
              y={7}
              anchor={0.5}
              style={{
                fontFamily: '"Courier New", monospace',
                fontSize: 8,
                fontWeight: "bold",
                fill: "#ffffff",
              }}
              resolution={2}
            />
            {/* Step name */}
            <pixiText
              text={stepId.slice(0, 34)}
              x={36}
              y={2}
              style={{
                fontFamily: '"Courier New", monospace',
                fontSize: 10,
                fontWeight: isActive ? "bold" : "normal",
                fill: isActive ? "#1f2937" : status === "completed" || status === "approved" ? "#6b7280" : "#374151",
              }}
              resolution={2}
            />
          </pixiContainer>
        );
      })}

      {/* Scroll indicator */}
      {stepIds.length > MAX_VISIBLE_STEPS && (
        <pixiText
          text={`${scrollOffset + 1}–${Math.min(scrollOffset + MAX_VISIBLE_STEPS, stepIds.length)}/${stepIds.length} steps`}
          x={width / 2}
          y={height - 6}
          anchor={{ x: 0.5, y: 1 }}
          style={{
            fontFamily: '"Courier New", monospace',
            fontSize: 9,
            fill: "#9ca3af",
          }}
          resolution={2}
        />
      )}
    </pixiContainer>
  );
}
