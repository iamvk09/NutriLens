import { jsPDF } from 'jspdf';
import autoTable from 'jspdf-autotable';
import { LoggedMeal } from '../types';

export function exportHealthPdf(userEmail: string, meals: LoggedMeal[]): void {
  const doc = new jsPDF();

  // Header Styling
  doc.setFont('helvetica', 'bold');
  doc.setFontSize(22);
  doc.setTextColor(16, 185, 129); // NutriLens Emerald
  doc.text('NutriLens Health Report', 105, 20, { align: 'center' });

  doc.setFont('helvetica', 'normal');
  doc.setFontSize(11);
  doc.setTextColor(100, 116, 139);
  doc.text(`User: ${userEmail}`, 105, 28, { align: 'center' });
  doc.text(`Generated: ${new Date().toLocaleDateString()}`, 105, 34, { align: 'center' });

  // Summary Metrics
  const totalCalories = meals.reduce((acc, m) => acc + (m.calories || 0), 0);
  const totalProtein = meals.reduce((acc, m) => acc + (m.protein_g || 0), 0);
  const avgCalories = meals.length > 0 ? Math.round(totalCalories / meals.length) : 0;

  doc.setDrawColor(226, 232, 240);
  doc.line(14, 40, 196, 40);

  doc.setFont('helvetica', 'bold');
  doc.setFontSize(12);
  doc.setTextColor(15, 23, 42);
  doc.text(`Total Meals Logged: ${meals.length}`, 14, 48);
  doc.text(`Total Energy: ${Math.round(totalCalories)} kcal`, 85, 48);
  doc.text(`Average Meal Cals: ${avgCalories} kcal`, 150, 48);
  doc.text(`Total Protein: ${Math.round(totalProtein)} g`, 14, 56);

  // Meals Table
  const tableData = meals.slice(0, 30).map((m) => [
    new Date(m.created_at).toLocaleDateString(),
    m.food_name,
    `${Math.round(m.calories)} kcal`,
    `${Math.round(m.protein_g)} g`,
    `${Math.round(m.fat_g)} g`,
    `${Math.round(m.carb_g)} g`,
  ]);

  autoTable(doc, {
    startY: 64,
    head: [['Date', 'Food Item', 'Calories', 'Protein', 'Fat', 'Carbs']],
    body: tableData,
    theme: 'grid',
    headStyles: {
      fillColor: [16, 185, 129],
      textColor: [255, 255, 255],
      fontStyle: 'bold',
    },
    styles: {
      fontSize: 9,
      cellPadding: 3,
    },
    alternateRowStyles: {
      fillColor: [248, 250, 252],
    },
  });

  doc.save(`NutriLens_Health_Report_${new Date().toISOString().slice(0, 10)}.pdf`);
}
