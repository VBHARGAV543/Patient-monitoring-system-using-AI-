package com.example.nursealarmapp.adapters

import android.graphics.Color
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.TextView
import androidx.cardview.widget.CardView
import androidx.core.content.ContextCompat
import androidx.recyclerview.widget.RecyclerView
import com.example.nursealarmapp.R
import com.example.nursealarmapp.models.Patient

class PatientAdapter(
    private var patients: List<Patient>,
    private val onPatientClick: (Patient) -> Unit
) : RecyclerView.Adapter<PatientAdapter.PatientViewHolder>() {

    class PatientViewHolder(view: View) : RecyclerView.ViewHolder(view) {
        val cardView: CardView = view.findViewById(R.id.cardPatient)
        val avatarText: TextView = view.findViewById(R.id.tvAvatar)
        val nameText: TextView = view.findViewById(R.id.tvPatientName)
        val statusText: TextView = view.findViewById(R.id.tvPatientStatus)
        val timestampText: TextView = view.findViewById(R.id.tvPatientTimestamp)
        val statusDot: View = view.findViewById(R.id.viewStatusDot)
    }

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): PatientViewHolder {
        val view = LayoutInflater.from(parent.context)
            .inflate(R.layout.item_patient, parent, false)
        return PatientViewHolder(view)
    }

    override fun onBindViewHolder(holder: PatientViewHolder, position: Int) {
        val patient = patients[position]
        val context = holder.itemView.context
        
        // Set avatar initial
        val initial = patient.name.firstOrNull()?.uppercase() ?: "P"
        holder.avatarText.text = initial
        
        holder.nameText.text = patient.name
        holder.statusText.text = patient.status
        holder.timestampText.text = patient.timestamp
        
        // Set colors based on status
        if (patient.fallDetected) {
            // Alert state - coral theme
            holder.cardView.setCardBackgroundColor(ContextCompat.getColor(context, R.color.cardBackground))
            holder.avatarText.backgroundTintList = ContextCompat.getColorStateList(context, R.color.coral)
            holder.nameText.setTextColor(ContextCompat.getColor(context, R.color.textPrimary))
            holder.statusText.setTextColor(ContextCompat.getColor(context, R.color.dangerRed))
            holder.statusDot.backgroundTintList = ContextCompat.getColorStateList(context, R.color.dangerRed)
        } else {
            // Stable state - green theme
            holder.cardView.setCardBackgroundColor(ContextCompat.getColor(context, R.color.cardBackground))
            holder.avatarText.backgroundTintList = ContextCompat.getColorStateList(context, R.color.navyBlue)
            holder.nameText.setTextColor(ContextCompat.getColor(context, R.color.textPrimary))
            holder.statusText.setTextColor(ContextCompat.getColor(context, R.color.successGreen))
            holder.statusDot.backgroundTintList = ContextCompat.getColorStateList(context, R.color.successGreen)
        }
        
        holder.cardView.setOnClickListener {
            onPatientClick(patient)
        }
    }

    override fun getItemCount() = patients.size

    fun updatePatients(newPatients: List<Patient>) {
        patients = newPatients
        notifyDataSetChanged()
    }
}
