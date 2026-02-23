package com.example.nursealarmapp.adapters

import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.TextView
import androidx.cardview.widget.CardView
import androidx.core.content.ContextCompat
import androidx.recyclerview.widget.RecyclerView
import com.example.nursealarmapp.R
import com.example.nursealarmapp.models.GeneralPatient

/**
 * Shows the full ADMITTED list (all 21 patients).
 * Each row: avatar, name, disease, attended-count badge, last attended timestamp.
 */
class AdmittedPatientAdapter(
    private var patients: List<GeneralPatient>,
    private val onPatientClick: (GeneralPatient) -> Unit
) : RecyclerView.Adapter<AdmittedPatientAdapter.VH>() {

    class VH(view: View) : RecyclerView.ViewHolder(view) {
        val card: CardView        = view.findViewById(R.id.cardAdmitted)
        val avatar: TextView      = view.findViewById(R.id.tvAdmAvatar)
        val name: TextView        = view.findViewById(R.id.tvAdmName)
        val realBadge: TextView   = view.findViewById(R.id.tvAdmRealBadge)
        val disease: TextView     = view.findViewById(R.id.tvAdmDisease)
        val attCount: TextView    = view.findViewById(R.id.tvAdmAttendedCount)
        val lastAtt: TextView     = view.findViewById(R.id.tvAdmLastAttended)
        val dot: View             = view.findViewById(R.id.viewAdmDot)
    }

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): VH {
        val v = LayoutInflater.from(parent.context)
            .inflate(R.layout.item_admitted_patient, parent, false)
        return VH(v)
    }

    override fun onBindViewHolder(holder: VH, position: Int) {
        val p = patients[position]
        val ctx = holder.itemView.context

        holder.avatar.text = p.name.firstOrNull()?.uppercase() ?: "P"
        holder.name.text = p.name
        holder.disease.text = p.disease

        // Real patient badge
        if (p.isReal) {
            holder.realBadge.visibility = View.VISIBLE
            holder.avatar.backgroundTintList =
                ContextCompat.getColorStateList(ctx, R.color.infoBlue)
        } else {
            holder.realBadge.visibility = View.GONE
            holder.avatar.backgroundTintList =
                ContextCompat.getColorStateList(ctx, R.color.navyBlue)
        }

        // Attended count
        val count = p.attendedTimestamps.size
        holder.attCount.text = "Attended: ${count}×"
        holder.lastAtt.text = if (count > 0) "Last: ${p.attendedTimestamps[0]}" else ""

        // Status dot colour
        val dotColor = if (p.isAlerted) R.color.dangerRed else R.color.successGreen
        holder.dot.backgroundTintList = ContextCompat.getColorStateList(ctx, dotColor)

        holder.card.setOnClickListener { onPatientClick(p) }
    }

    override fun getItemCount() = patients.size

    fun update(newList: List<GeneralPatient>) {
        patients = newList
        notifyDataSetChanged()
    }
}
