/*
 * Python Heimdal
 *	Bindings for the ticket object of heimdal
 *
 * Copyright 2003-2019 Univention GmbH
 *
 * https://www.univention.de/
 *
 * All rights reserved.
 *
 * The source code of this program is made available
 * under the terms of the GNU Affero General Public License version 3
 * (GNU AGPL V3) as published by the Free Software Foundation.
 *
 * Binary versions of this program provided by Univention to you as
 * well as other copyrighted, protected or trademarked materials like
 * Logos, graphics, fonts, specific documentations and configurations,
 * cryptographic keys etc. are subject to a license agreement between
 * you and Univention and not subject to the GNU AGPL V3.
 *
 * In the case you use this program under the terms of the GNU AGPL V3,
 * the program is provided in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
 * GNU Affero General Public License for more details.
 *
 * You should have received a copy of the GNU Affero General Public
 * License with the Debian GNU/Linux or Univention distribution in file
 * /usr/share/common-licenses/AGPL-3; if not, see
 * <https://www.gnu.org/licenses/>.
 */

#include <Python.h>

#include <krb5.h>

#include "error.h"
#include "context.h"
#include "ticket.h"

krb5TicketObject *ticket_new(PyObject *unused, PyObject *args)
{
	krb5ContextObject *context;
	if (!PyArg_ParseTuple(args, "O", &context))
		return NULL;

	krb5TicketObject *self = (krb5TicketObject *) PyObject_New(krb5TicketObject, &krb5TicketType);
	if (self == NULL)
		return NULL;

	self->context = context->context;

	return self;
}

static void ticket_destroy(krb5TicketObject *self)
{
	krb5_free_ticket(self->context, &self->ticket);
	PyObject_Del(self);
}

PyTypeObject krb5TicketType = {
	PyVarObject_HEAD_INIT(&PyType_Type, 0)
	.tp_name = "heimdal.krb5Ticket",
	.tp_basicsize = sizeof(krb5TicketObject),
	/* methods */
	.tp_dealloc = (destructor)ticket_destroy,
};

//static struct PyMethodDef ticket_methods[] = {};
