/*
 * Copyright (c) 2015.
 * All rights reserved.
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions
 * are met:
 * 1. Redistributions of source code must retain the above copyright
 *    notice, this list of conditions and the following disclaimer.
 * 2. Redistributions in binary form must reproduce the above copyright
 *    notice, this list of conditions and the following disclaimer in the
 *    documentation and/or other materials provided with the distribution.
 * 3. Neither the name of the Institute nor the names of its contributors
 *    may be used to endorse or promote products derived from this software
 *    without specific prior written permission.
 *
 * THIS SOFTWARE IS PROVIDED BY THE INSTITUTE AND CONTRIBUTORS ``AS IS'' AND
 * ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
 * IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
 * ARE DISCLAIMED.  IN NO EVENT SHALL THE INSTITUTE OR CONTRIBUTORS BE LIABLE
 * FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
 * DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS
 * OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
 * HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
 * LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY
 * OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF
 * SUCH DAMAGE.
 *
 *
 */

/**
 * \file
 *         Puts the openmote in the deepest power-saving mode forever
 * \author
 *         Beshr Al Nahas <beshr@chalmers.se>
 */

#include "contiki.h"

#include <stdio.h> /* For printf() */
#include "dev/leds.h"
#include "clock.h"
#include "cpu.h"
#include "reg.h"
#include "dev/sys-ctrl.h"
#include "net/netstack.h"

#define assert_wfi() do { asm("wfi"::); } while(0)

static void
select_16_mhz_rcosc(void)
{
  /*
   * Power up both oscillators in order to speed up the transition to the 32-MHz
   * XOSC after wake up.
   */
  REG(SYS_CTRL_CLOCK_CTRL) &= ~SYS_CTRL_CLOCK_CTRL_OSC_PD;

  /*First, make sure there is no ongoing clock source change */
  while((REG(SYS_CTRL_CLOCK_STA) & SYS_CTRL_CLOCK_STA_SOURCE_CHANGE) != 0);

  /* Set the System Clock to use the 16MHz RC OSC */
  REG(SYS_CTRL_CLOCK_CTRL) |= SYS_CTRL_CLOCK_CTRL_OSC;

  /* Wait till it's happened */
  while((REG(SYS_CTRL_CLOCK_STA) & SYS_CTRL_CLOCK_STA_OSC) == 0);
}

/*---------------------------------------------------------------------------*/
PROCESS(deepsleep_process, "Deep sleep process");
AUTOSTART_PROCESSES(&deepsleep_process);
/*---------------------------------------------------------------------------*/
PROCESS_THREAD(deepsleep_process, ev, data)
{
  PROCESS_BEGIN();

  while(1) {
    printf("Putting mote in deep sleep-3 forever. Sleeping in 0.5 seconds\n");
    clock_wait(CLOCK_SECOND/2);
    NETSTACK_MAC.off(0);
    leds_off(LEDS_ALL);
    /* Going to deep sleep PM3 -- point of no return */
    INTERRUPTS_DISABLE();
    select_16_mhz_rcosc();
    REG(SYS_CTRL_PMCTL) = SYS_CTRL_PMCTL_PM3;
    assert_wfi();
  }
  PROCESS_END();
}
/*---------------------------------------------------------------------------*/
